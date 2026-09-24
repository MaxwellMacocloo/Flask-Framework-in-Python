"""Server-rendered pages. Jinja2 templates, forms, redirects."""

from flask import Blueprint, abort, redirect, render_template, request, url_for

from . import store

web = Blueprint("web", __name__)


@web.route("/")
def index():
    """Dashboard: every student plus the class summary."""
    return render_template(
        "index.html",
        students=store.list_students(),
        summary=store.class_summary(),
        subjects=store.SUBJECTS,
    )


@web.route("/about")
def about():
    return render_template("about.html", subjects=store.SUBJECTS)


@web.route("/submit", methods=["GET", "POST"])
def submit():
    """The score-entry form.

    GET renders the form. POST validates it, stores the student, then
    redirects to the result page. Redirecting after a successful POST
    means a browser refresh does not submit the form twice.
    """
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        errors = []

        if not name:
            errors.append("Name is required.")

        scores = {}
        for subject in store.SUBJECTS:
            raw = request.form.get(subject, "").strip() or "0"
            try:
                value = float(raw)
            except ValueError:
                errors.append(f"{subject.replace('_', ' ').title()} must be a number.")
                continue
            if not 0 <= value <= 100:
                errors.append(f"{subject.replace('_', ' ').title()} must be between 0 and 100.")
                continue
            scores[subject] = value

        if errors:
            # Re-render the form with the errors and the values already typed.
            return render_template(
                "submit.html",
                subjects=store.SUBJECTS,
                errors=errors,
                submitted=request.form,
            ), 400

        student = store.add_student(name, scores)
        return redirect(url_for("web.result", student_id=student["id"]))

    return render_template("submit.html", subjects=store.SUBJECTS,
                           errors=[], submitted={})


@web.route("/result/<int:student_id>")
def result(student_id):
    """Scorecard for one student."""
    student = store.get_student(student_id)
    if student is None:
        abort(404)
    return render_template("result.html", student=student,
                           pass_mark=store.PASS_MARK)


@web.route("/delete/<int:student_id>", methods=["POST"])
def delete(student_id):
    store.delete_student(student_id)
    return redirect(url_for("web.index"))
