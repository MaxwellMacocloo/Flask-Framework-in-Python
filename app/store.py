"""In-memory data store for student records.

Kept deliberately simple: a module-level list plus an id counter. Swapping
this for SQLite means changing only this file, because nothing else in the
app touches the data directly.
"""

import threading

# Every subject contributes equally to the final average.
SUBJECTS = ["science", "maths", "programming", "data_science", "physics"]

PASS_MARK = 50.0

_lock = threading.Lock()
_students = []
_next_id = 1


def _grade(average):
    """Map a numeric average onto a letter grade."""
    if average >= 80:
        return "A"
    if average >= 70:
        return "B"
    if average >= 60:
        return "C"
    if average >= PASS_MARK:
        return "D"
    return "F"


def build_record(name, scores):
    """Compute the derived fields for one student.

    `scores` maps subject name to mark. Missing subjects count as 0 so a
    partially filled form still produces a valid record.
    """
    marks = {subject: float(scores.get(subject, 0)) for subject in SUBJECTS}
    total = sum(marks.values())
    average = total / len(SUBJECTS)

    return {
        "name": name,
        "scores": marks,
        "total": round(total, 2),
        "average": round(average, 2),
        "grade": _grade(average),
        "result": "Pass" if average >= PASS_MARK else "Fail",
    }


def add_student(name, scores):
    """Store a new student and return the saved record, id included."""
    global _next_id

    record = build_record(name, scores)
    with _lock:
        record["id"] = _next_id
        _next_id += 1
        _students.append(record)
    return record


def list_students():
    """Return every stored student."""
    return list(_students)


def get_student(student_id):
    """Return one student by id, or None."""
    return next((s for s in _students if s["id"] == student_id), None)


def update_student(student_id, name=None, scores=None):
    """Update a student in place. Returns the updated record, or None."""
    student = get_student(student_id)
    if student is None:
        return None

    merged = dict(student["scores"])
    if scores:
        merged.update({k: v for k, v in scores.items() if k in SUBJECTS})

    recomputed = build_record(name or student["name"], merged)
    student.update(recomputed)
    return student


def delete_student(student_id):
    """Remove a student. Returns True if one was removed."""
    student = get_student(student_id)
    if student is None:
        return False
    _students.remove(student)
    return True


def class_summary():
    """Aggregate statistics across every stored student."""
    if not _students:
        return {"students": 0}

    averages = [s["average"] for s in _students]
    return {
        "students": len(_students),
        "class_average": round(sum(averages) / len(averages), 2),
        "highest": round(max(averages), 2),
        "lowest": round(min(averages), 2),
        "passed": sum(1 for s in _students if s["result"] == "Pass"),
        "failed": sum(1 for s in _students if s["result"] == "Fail"),
    }


def reset(seed=True):
    """Clear the store. Used by the tests and at app startup."""
    global _students, _next_id
    with _lock:
        _students = []
        _next_id = 1
    if seed:
        add_student("Ama Mensah", {"science": 88, "maths": 92, "programming": 79,
                                   "data_science": 85, "physics": 81})
        add_student("Kofi Boateng", {"science": 61, "maths": 55, "programming": 72,
                                     "data_science": 48, "physics": 59})
        add_student("Yayra Dogbe", {"science": 42, "maths": 38, "programming": 51,
                                    "data_science": 45, "physics": 40})
