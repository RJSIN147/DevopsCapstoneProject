def test_create_and_list_doctors(client, doctor):
    res = client.get("/api/doctors")
    assert res.status_code == 200
    names = [d["full_name"] for d in res.json()]
    assert names == ["Dr. Test Doctor"]


def test_get_unknown_doctor_returns_404(client):
    assert client.get("/api/doctors/999").status_code == 404


def test_update_doctor_room_and_deactivate(client, doctor):
    res = client.put(f"/api/doctors/{doctor['id']}", json={"room": "305", "active": False})
    assert res.status_code == 200
    assert res.json()["room"] == "305"
    assert res.json()["active"] is False

    active_only = client.get("/api/doctors", params={"active": True}).json()
    assert active_only == []


def test_doctor_validation(client):
    res = client.post("/api/doctors", json={"full_name": "X", "specialty": ""})
    assert res.status_code == 422


def test_cannot_delete_doctor_with_appointments(client, doctor, book):
    assert book().status_code == 201
    res = client.delete(f"/api/doctors/{doctor['id']}")
    assert res.status_code == 409


def test_delete_doctor_without_appointments(client, doctor):
    assert client.delete(f"/api/doctors/{doctor['id']}").status_code == 204
    assert client.get(f"/api/doctors/{doctor['id']}").status_code == 404
