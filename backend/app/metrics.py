from prometheus_client import Counter

# no specialty/doctor label on purpose: those are free text from users and would let
# anyone blow up the number of time series Prometheus has to store
appointments_booked = Counter(
    "clinicdesk_appointments_booked_total",
    "Appointments booked through the API",
)

appointment_status_changes = Counter(
    "clinicdesk_appointment_status_changes_total",
    "Appointment status transitions",
    ["status"],
)

booking_conflicts = Counter(
    "clinicdesk_booking_conflicts_total",
    "Bookings rejected because the doctor already had that slot",
)
