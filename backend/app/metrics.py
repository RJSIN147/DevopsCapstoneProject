from prometheus_client import Counter

appointments_booked = Counter(
    "clinicdesk_appointments_booked_total",
    "Appointments booked through the API",
    ["specialty"],
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
