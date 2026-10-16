from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

AppointmentStatus = Literal["BOOKED", "CHECKED_IN", "COMPLETED", "CANCELLED"]


def as_utc(value: datetime) -> datetime:
    # sqlite hands back naive datetimes, so treat anything without tzinfo as UTC
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class DoctorBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    specialty: str = Field(min_length=2, max_length=80)
    room: str = Field(default="", max_length=20)
    active: bool = True


class DoctorCreate(DoctorBase):
    pass


class DoctorUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    specialty: str | None = Field(default=None, min_length=2, max_length=80)
    room: str | None = Field(default=None, max_length=20)
    active: bool | None = None


class DoctorOut(DoctorBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class AppointmentBase(BaseModel):
    patient_name: str = Field(min_length=2, max_length=120)
    patient_phone: str = Field(default="", max_length=20, pattern=r"^[0-9+\-\s]*$")
    doctor_id: int
    scheduled_at: datetime
    duration_minutes: int = Field(default=20, ge=5, le=240)
    reason: str = Field(default="", max_length=500)

    @field_validator("scheduled_at")
    @classmethod
    def normalise_time(cls, value: datetime) -> datetime:
        return as_utc(value)


class AppointmentCreate(AppointmentBase):
    status: AppointmentStatus = "BOOKED"


class AppointmentUpdate(BaseModel):
    patient_name: str | None = Field(default=None, min_length=2, max_length=120)
    patient_phone: str | None = Field(default=None, max_length=20, pattern=r"^[0-9+\-\s]*$")
    doctor_id: int | None = None
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=5, le=240)
    reason: str | None = Field(default=None, max_length=500)
    status: AppointmentStatus | None = None

    @field_validator("scheduled_at")
    @classmethod
    def normalise_time(cls, value: datetime | None) -> datetime | None:
        return as_utc(value) if value else value


class AppointmentOut(AppointmentBase):
    id: int
    status: AppointmentStatus
    doctor_name: str
    specialty: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("created_at")
    @classmethod
    def created_utc(cls, value: datetime) -> datetime:
        return as_utc(value)


class StatsOut(BaseModel):
    total: int
    today: int
    booked: int
    checkedIn: int
    completed: int
    cancelled: int
    activeDoctors: int
