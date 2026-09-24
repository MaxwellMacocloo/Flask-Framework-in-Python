"""Tests for both the web pages and the JSON API.

Run with:  pytest -v
"""

import pytest

from app import create_app, store


@pytest.fixture
def client():
    app = create_app(seed=True)
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ---------------------------------------------------------------- web pages

def test_dashboard_lists_seeded_students(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Ama Mensah" in response.data
    assert b"Class summary" in response.data


def test_submit_page_renders_form(client):
    response = client.get("/submit")
    assert response.status_code == 200
    assert b"Enter scores" in response.data
    # Every subject must have an input.
    for subject in store.SUBJECTS:
        assert subject.encode() in response.data


def test_submit_post_redirects_to_result(client):
    response = client.post("/submit", data={
        "name": "Test Student",
        "science": "80", "maths": "70", "programming": "90",
        "data_science": "60", "physics": "75",
    })
    assert response.status_code == 302
    assert "/result/" in response.headers["Location"]

    # Follow through and confirm the computed average appears.
    page = client.get(response.headers["Location"])
    assert page.status_code == 200
    assert b"Test Student" in page.data
    assert b"75.0" in page.data  # (80+70+90+60+75)/5


def test_submit_rejects_out_of_range_score(client):
    response = client.post("/submit", data={"name": "Bad", "science": "150"})
    assert response.status_code == 400
    assert b"between 0 and 100" in response.data


def test_submit_rejects_missing_name(client):
    response = client.post("/submit", data={"science": "50"})
    assert response.status_code == 400
    assert b"Name is required" in response.data


def test_unknown_student_returns_html_404(client):
    response = client.get("/result/9999")
    assert response.status_code == 404
    assert b"404" in response.data


# ----------------------------------------------------------------- JSON API

def test_api_list_students(client):
    response = client.get("/api/students")
    assert response.status_code == 200
    body = response.get_json()
    assert len(body) == 3
    assert body[0]["name"] == "Ama Mensah"


def test_api_get_single_student(client):
    response = client.get("/api/students/1")
    assert response.status_code == 200
    assert response.get_json()["grade"] == "A"


def test_api_create_student(client):
    response = client.post("/api/students", json={
        "name": "Nana Adjei",
        "scores": {"science": 90, "maths": 90, "programming": 90,
                   "data_science": 90, "physics": 90},
    })
    assert response.status_code == 201
    body = response.get_json()
    assert body["average"] == 90.0
    assert body["grade"] == "A"
    assert body["result"] == "Pass"
    assert body["id"] == 4


def test_api_create_requires_name(client):
    response = client.post("/api/students", json={"scores": {"maths": 50}})
    assert response.status_code == 400
    assert "name" in response.get_json()["error"]


def test_api_create_rejects_unknown_subject(client):
    response = client.post("/api/students", json={
        "name": "X", "scores": {"astrology": 100},
    })
    assert response.status_code == 400
    assert "Unknown subject" in response.get_json()["details"][0]


def test_api_update_recomputes_grade(client):
    # Yayra starts as a fail; raise every mark and the grade must follow.
    before = client.get("/api/students/3").get_json()
    assert before["result"] == "Fail"

    response = client.put("/api/students/3", json={
        "scores": {"science": 85, "maths": 85, "programming": 85,
                   "data_science": 85, "physics": 85},
    })
    assert response.status_code == 200
    after = response.get_json()
    assert after["average"] == 85.0
    assert after["result"] == "Pass"
    assert after["grade"] == "A"


def test_api_update_missing_student(client):
    response = client.put("/api/students/9999", json={"scores": {"maths": 50}})
    assert response.status_code == 404


def test_api_delete_student(client):
    assert client.delete("/api/students/2").status_code == 200
    assert client.get("/api/students/2").status_code == 404
    assert len(client.get("/api/students").get_json()) == 2


def test_api_delete_missing_student(client):
    assert client.delete("/api/students/9999").status_code == 404


def test_api_summary(client):
    body = client.get("/api/summary").get_json()
    assert body["students"] == 3
    assert body["passed"] == 2
    assert body["failed"] == 1


def test_api_404_returns_json_not_html(client):
    response = client.get("/api/nonexistent")
    assert response.status_code == 404
    assert response.get_json()["error"] == "Not found"


# ------------------------------------------------------------- grade logic

@pytest.mark.parametrize("mark,expected_grade,expected_result", [
    (95, "A", "Pass"),
    (80, "A", "Pass"),
    (75, "B", "Pass"),
    (65, "C", "Pass"),
    (50, "D", "Pass"),
    (49.9, "F", "Fail"),
    (0, "F", "Fail"),
])
def test_grade_boundaries(mark, expected_grade, expected_result):
    record = store.build_record("Boundary", {s: mark for s in store.SUBJECTS})
    assert record["grade"] == expected_grade
    assert record["result"] == expected_result


def test_missing_subjects_count_as_zero():
    record = store.build_record("Partial", {"maths": 100})
    assert record["total"] == 100.0
    assert record["average"] == 20.0
    assert record["scores"]["science"] == 0.0
