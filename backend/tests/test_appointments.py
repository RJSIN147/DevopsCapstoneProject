from datetime import timedelta


def test_book_appointment(book, doctor):
    res = book()
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "BOOKED"
    assert body["doctor_name"] == doctor["full_name"]
    assert body["specialty"] == "General Medicine"


def test_get_appointment_by_id(client, book):
    appt = book().json()
    res = client.get(f"/api/appointments/{appt['id']}")
    assert res.status_code == 200
    assert res.json()["patient_name"] == "Riya Sharma"


def test_unknown_appointment_returns_404(client):
    assert client.get("/api/appointments/12345").status_code == 404
    assert client.put("/api/appointments/12345", json={"status": "COMPLETED"}).status_code == 404
    assert client.delete("/api/appointments/12345").status_code == 404


def test_booking_needs_existing_doctor(book):
    assert book(doctor_id=999).status_code == 404


def test_booking_rejects_bad_payload(book):
    assert book(patient_name="").status_code == 422
    assert book(duration_minutes=1).status_code == 422
    assert book(patient_phone="call me maybe").status_code == 422


def test_double_booking_same_doctor_is_rejected(book, slot):
    assert book().status_code == 201
    overlapping = book(patient_name="Arjun Verma", scheduled_at=(slot + timedelta(minutes=10)).isoformat())
    assert overlapping.status_code == 409


def test_back_to_back_slots_are_allowed(book, slot):
    assert book().status_code == 201
    next_slot = book(patient_name="Arjun Verma", scheduled_at=(slot + timedelta(minutes=20)).isoformat())
    assert next_slot.status_code == 201


def test_cancelled_slot_can_be_rebooked(client, book):
    first = book().json()
    client.put(f"/api/appointments/{first['id']}", json={"status": "CANCELLED"})
    assert book(patient_name="Arjun Verma").status_code == 201


def test_inactive_doctor_cannot_take_bookings(client, doctor, book):
    client.put(f"/api/doctors/{doctor['id']}", json={"active": False})
    assert book().status_code == 422


def test_update_status_flow(client, book):
    appt = book().json()
    for status in ["CHECKED_IN", "COMPLETED"]:
        res = client.put(f"/api/appointments/{appt['id']}", json={"status": status})
        assert res.status_code == 200
        assert res.json()["status"] == status


def test_reschedule_into_taken_slot_is_rejected(client, book, slot):
    book()
    later = book(patient_name="Arjun Verma", scheduled_at=(slot + timedelta(hours=1)).isoformat()).json()
    res = client.put(f"/api/appointments/{later['id']}", json={"scheduled_at": slot.isoformat()})
    assert res.status_code == 409


def test_list_filters_by_status_and_day(client, book, slot):
    a = book().json()
    book(patient_name="Arjun Verma", scheduled_at=(slot + timedelta(days=1)).isoformat())
    client.put(f"/api/appointments/{a['id']}", json={"status": "CHECKED_IN"})

    checked_in = client.get("/api/appointments", params={"status": "CHECKED_IN"}).json()
    assert [x["id"] for x in checked_in] == [a["id"]]

    on_day = client.get("/api/appointments", params={"on": slot.date().isoformat()}).json()
    assert len(on_day) == 1


def test_delete_appointment(client, book):
    appt = book().json()
    assert client.delete(f"/api/appointments/{appt['id']}").status_code == 204
    assert client.get(f"/api/appointments/{appt['id']}").status_code == 404


def test_stats(client, book, slot):
    a = book().json()
    book(patient_name="Arjun Verma", scheduled_at=(slot + timedelta(hours=2)).isoformat())
    client.put(f"/api/appointments/{a['id']}", json={"status": "COMPLETED"})

    stats = client.get("/api/appointments/stats").json()
    assert stats["total"] == 2
    assert stats["booked"] == 1
    assert stats["completed"] == 1
    assert stats["activeDoctors"] == 1


def test_day_filter_uses_clinic_timezone(client, book, slot):
    # 20:00 UTC is already 01:30 the next morning in Asia/Kolkata (the default clinic timezone)
    late = slot.replace(hour=20, minute=0)
    appt = book(scheduled_at=late.isoformat()).json()

    next_local_day = (late + timedelta(days=1)).date().isoformat()
    same_utc_day = late.date().isoformat()

    assert [a["id"] for a in client.get("/api/appointments", params={"on": next_local_day}).json()] == [appt["id"]]
    assert client.get("/api/appointments", params={"on": same_utc_day}).json() == []
