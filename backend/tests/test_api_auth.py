"""Integration tests for authentication endpoints."""


class TestLogin:
    def test_teacher_login(self, client, teacher):
        resp = client.post("/api/auth/login", json={
            "username": "test.teacher",
            "password": "password",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["user"]["role"] == "teacher"
        assert data["user"]["username"] == "test.teacher"

    def test_student_login(self, client, student):
        resp = client.post("/api/auth/login", json={
            "username": "test.student",
            "password": "password",
        })
        assert resp.status_code == 200
        assert resp.json()["user"]["role"] == "student"

    def test_invalid_password(self, client, teacher):
        resp = client.post("/api/auth/login", json={
            "username": "test.teacher",
            "password": "wrong",
        })
        assert resp.status_code == 401

    def test_nonexistent_user(self, client):
        resp = client.post("/api/auth/login", json={
            "username": "nobody",
            "password": "password",
        })
        assert resp.status_code == 401


class TestMe:
    def test_get_me_authenticated(self, client, auth_teacher, teacher):
        resp = client.get("/api/auth/me", headers=auth_teacher)
        assert resp.status_code == 200
        assert resp.json()["first_name"] == "Test"

    def test_get_me_unauthenticated(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401


class TestRegister:
    def test_register_teacher(self, client):
        resp = client.post("/api/auth/register", json={
            "first_name": "New",
            "last_name": "Teacher",
            "username": "new.teacher",
            "email": "new@test.com",
            "password": "securepass",
            "role": "teacher",
        })
        assert resp.status_code == 200
        assert resp.json()["user"]["role"] == "teacher"

    def test_register_student_rejected(self, client):
        resp = client.post("/api/auth/register", json={
            "first_name": "Bad",
            "last_name": "Actor",
            "username": "bad.actor",
            "password": "pass",
            "role": "student",
        })
        assert resp.status_code == 400
