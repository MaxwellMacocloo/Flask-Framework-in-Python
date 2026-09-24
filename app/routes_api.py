"""JSON REST API covering all five HTTP verbs used in the course.

GET    /api/students        list
GET    /api/students/<id>   fetch one
POST   /api/students        create
PUT    /api/students/<id>   replace/update
DELETE /api/students/<id>   remove
GET    /api/summary         class aggregate
"""

from flask import Blueprint, jsonify, request

from . import store

api = Blueprint("api", __name__, url_prefix="/api")


def _validate_scores(payload):
    """Return (scores, errors) after checking every submitted subject."""
    scores, errors = {}, []

    for subject, value in (payload.get("scores") or {}).items():
        if subject not in store.SUBJECTS:
            errors.append(f"Unknown subject: {subject}")
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            errors.append(f"{subject} must be a number")
            continue
        if not 0 <= number <= 100:
            errors.append(f"{subject} must be between 0 and 100")
            continue
        scores[subject] = number

    return scores, errors


@api.get("/students")
def list_students():
    return jsonify(store.list_students())


@api.get("/students/<int:student_id>")
def get_student(student_id):
    student = store.get_student(student_id)
    if student is None:
        return jsonify({"error": "Student not found"}), 404
    return jsonify(student)


@api.post("/students")
def create_student():
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "JSON body required"}), 400

    name = (payload.get("name") or "").strip()
    if not name:
        return jsonify({"error": "'name' is required"}), 400

    scores, errors = _validate_scores(payload)
    if errors:
        return jsonify({"error": "Invalid scores", "details": errors}), 400

    return jsonify(store.add_student(name, scores)), 201


@api.put("/students/<int:student_id>")
def update_student(student_id):
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"error": "JSON body required"}), 400

    scores, errors = _validate_scores(payload)
    if errors:
        return jsonify({"error": "Invalid scores", "details": errors}), 400

    student = store.update_student(student_id, payload.get("name"), scores)
    if student is None:
        return jsonify({"error": "Student not found"}), 404
    return jsonify(student)


@api.delete("/students/<int:student_id>")
def delete_student(student_id):
    if not store.delete_student(student_id):
        return jsonify({"error": "Student not found"}), 404
    return jsonify({"result": "Student deleted", "id": student_id})


@api.get("/summary")
def summary():
    return jsonify(store.class_summary())
