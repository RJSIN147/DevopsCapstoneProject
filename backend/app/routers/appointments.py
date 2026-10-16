from datetime import UTC, date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from .. import metrics
from ..db import get_db
from ..models import Appointment, Doctor
from ..schemas import AppointmentCreate, AppointmentOut, AppointmentStatus, AppointmentUpdate, StatsOut, as_utc

router = APIRouter(prefix="/api/appointments", tags=["appointments"])


def get_appointment_or_404(db: Session, appointment_id: int) -> Appointment:
    appt = db.get(Appointment, appointment_id, options=[joinedload(Appointment.doctor)])
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appt


def check_doctor(db: Session, doctor_id: int) -> Doctor:
    doctor = db.get(Doctor, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    if not doctor.active:
        raise HTTPException(status_code=422, detail="Doctor is not taking appointments")
    return doctor


def check_slot_free(db: Session, doctor_id: int, start: datetime, minutes: int, ignore_id: int | None = None):
    """Reject the booking if it overlaps another live appointment for the same doctor."""
    end = start + timedelta(minutes=minutes)
    # nobody books longer than 4h so this window is enough to catch every overlap
    query = select(Appointment).where(
        Appointment.doctor_id == doctor_id,
        Appointment.status != "CANCELLED",
        Appointment.scheduled_at > start - timedelta(hours=4),
        Appointment.scheduled_at < end,
    )
    if ignore_id is not None:
        query = query.where(Appointment.id != ignore_id)

    for other in db.scalars(query):
        other_start = as_utc(other.scheduled_at)
        other_end = other_start + timedelta(minutes=other.duration_minutes)
        if other_start < end and start < other_end:
            metrics.booking_conflicts.inc()
            raise HTTPException(
                status_code=409,
                detail=f"Doctor already has an appointment at {other_start:%H:%M} UTC",
            )


def day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=UTC)
    return start, start + timedelta(days=1)


@router.get("", response_model=list[AppointmentOut])
def list_appointments(
    status_filter: AppointmentStatus | None = Query(default=None, alias="status"),
    doctor_id: int | None = None,
    on: date | None = Query(default=None, description="Only appointments on this day (UTC)"),
    db: Session = Depends(get_db),
):
    query = select(Appointment).options(joinedload(Appointment.doctor)).order_by(Appointment.scheduled_at)
    if status_filter:
        query = query.where(Appointment.status == status_filter)
    if doctor_id:
        query = query.where(Appointment.doctor_id == doctor_id)
    if on:
        start, end = day_bounds(on)
        query = query.where(Appointment.scheduled_at >= start, Appointment.scheduled_at < end)
    return list(db.scalars(query))


@router.get("/stats", response_model=StatsOut)
def appointment_stats(db: Session = Depends(get_db)):
    rows = db.execute(select(Appointment.status, func.count(Appointment.id)).group_by(Appointment.status)).all()
    counts = dict(rows)
    start, end = day_bounds(datetime.now(UTC).date())
    today = db.scalar(
        select(func.count(Appointment.id)).where(
            Appointment.scheduled_at >= start,
            Appointment.scheduled_at < end,
            Appointment.status != "CANCELLED",
        )
    )
    active_doctors = db.scalar(select(func.count(Doctor.id)).where(Doctor.active.is_(True)))
    return StatsOut(
        total=sum(counts.values()),
        today=today or 0,
        booked=counts.get("BOOKED", 0),
        checkedIn=counts.get("CHECKED_IN", 0),
        completed=counts.get("COMPLETED", 0),
        cancelled=counts.get("CANCELLED", 0),
        activeDoctors=active_doctors or 0,
    )


@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: int, db: Session = Depends(get_db)):
    return get_appointment_or_404(db, appointment_id)


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    check_doctor(db, payload.doctor_id)
    if payload.status != "CANCELLED":
        check_slot_free(db, payload.doctor_id, payload.scheduled_at, payload.duration_minutes)

    appt = Appointment(**payload.model_dump())
    db.add(appt)
    db.commit()
    db.refresh(appt)
    metrics.appointments_booked.inc()
    return appt


@router.put("/{appointment_id}", response_model=AppointmentOut)
def update_appointment(appointment_id: int, payload: AppointmentUpdate, db: Session = Depends(get_db)):
    appt = get_appointment_or_404(db, appointment_id)
    changes = payload.model_dump(exclude_unset=True)

    if "doctor_id" in changes and changes["doctor_id"] != appt.doctor_id:
        check_doctor(db, changes["doctor_id"])

    new_status = changes.get("status", appt.status)
    if new_status != "CANCELLED" and {"doctor_id", "scheduled_at", "duration_minutes", "status"} & changes.keys():
        check_slot_free(
            db,
            changes.get("doctor_id", appt.doctor_id),
            changes.get("scheduled_at") or as_utc(appt.scheduled_at),
            changes.get("duration_minutes", appt.duration_minutes),
            ignore_id=appt.id,
        )

    if "status" in changes and changes["status"] != appt.status:
        metrics.appointment_status_changes.labels(status=changes["status"]).inc()

    for key, value in changes.items():
        setattr(appt, key, value)
    db.commit()
    db.refresh(appt)
    return appt


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appt = get_appointment_or_404(db, appointment_id)
    db.delete(appt)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
