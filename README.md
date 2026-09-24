# Flask Scorecard + REST API

A Flask app that records student marks across five subjects, computes an
average and a letter grade, and exposes the same data two ways: as
server-rendered Jinja2 pages and as a JSON REST API.

**25 passing tests** cover both surfaces.

```bash
pip install -r requirements.txt
python run.py          # http://127.0.0.1:5000
pytest -v              # run the tests
```

## The web app

| Route | Method | Page |
|---|---|---|
| `/` | GET | Dashboard: all students, class summary cards |
| `/submit` | GET, POST | Score-entry form; POST validates then redirects |
| `/result/<id>` | GET | One student's scorecard with inline bar chart |
| `/about` | GET | Subjects and grade boundaries |
| `/delete/<id>` | POST | Remove a student |

## The REST API

| Route | Method | Purpose |
|---|---|---|
| `/api/students` | GET | List every student |
| `/api/students/<id>` | GET | Fetch one |
| `/api/students` | POST | Create (201, or 400 on bad input) |
| `/api/students/<id>` | PUT | Update; average and grade are recomputed |
| `/api/students/<id>` | DELETE | Remove |
| `/api/summary` | GET | Class aggregate |

```bash
# Create a student
curl -X POST http://127.0.0.1:5000/api/students \
  -H "Content-Type: application/json" \
  -d '{"name":"Nana Adjei","scores":{"science":90,"maths":88,"programming":95,"data_science":91,"physics":86}}'

# Response: 201
# {"id":4,"name":"Nana Adjei","average":90.0,"grade":"A","result":"Pass",
#  "total":450.0,"scores":{...}}

# Raise one student's marks; the grade follows automatically
curl -X PUT http://127.0.0.1:5000/api/students/3 \
  -H "Content-Type: application/json" \
  -d '{"scores":{"science":85,"maths":85,"programming":85,"data_science":85,"physics":85}}'

curl http://127.0.0.1:5000/api/summary
# {"students":4,"class_average":79.75,"highest":90.0,"lowest":59.0,"passed":4,"failed":0}
```

## Things worth pointing out

**The app factory.** `create_app()` builds the app inside a function
instead of at import time, so every test gets a fresh instance with a clean
data store. That is what makes the 25 tests independent of each other.

**Blueprints split the two surfaces.** Web routes live in
[`app/routes_web.py`](app/routes_web.py), API routes in
[`app/routes_api.py`](app/routes_api.py) under a `/api` prefix. Both read
from the same [`app/store.py`](app/store.py), so the HTML and the JSON can
never disagree about a student's grade.

**Content-negotiated 404s.** One error handler serves both surfaces:

```python
@app.errorhandler(404)
def not_found(error):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not found", "path": request.path}), 404
    return render_template("404.html"), 404
```

A browser hitting a bad URL gets the styled page; a `curl` against
`/api/nonexistent` gets JSON. Both are tested.

**Redirect after POST.** A successful form submission returns a 302 to
`/result/<id>` rather than rendering the page directly. Without this, a
browser refresh resubmits the form and creates a duplicate student.

**Failed validation preserves input.** A rejected form re-renders with a
400 and the values already typed, so the user does not start over:

```python
return render_template("submit.html", errors=errors, submitted=request.form), 400
```

**Template inheritance.** All five pages extend `base.html`, which holds
the nav, the stylesheet link and the footer. Adding a nav item is a
one-line change, not five.

## Layout

```
flask-scorecard-api/
├── run.py                   dev server entry point
├── test_app.py              25 tests
├── app/
│   ├── __init__.py          create_app() factory + error handlers
│   ├── store.py             data + grade logic (no Flask imports)
│   ├── routes_web.py        Jinja2 pages
│   ├── routes_api.py        JSON REST API
│   ├── templates/           base, index, submit, result, about, 404
│   └── static/style.css     responsive, no framework
└── requirements.txt
```

`store.py` imports nothing from Flask, so the grade logic is testable
without an app context — see the `test_grade_boundaries` parametrised test.

## Grade boundaries

| Average | Grade | Result |
|---|---|---|
| 80+ | A | Pass |
| 70–79 | B | Pass |
| 60–69 | C | Pass |
| 50–59 | D | Pass |
| < 50 | F | Fail |

Data is held in memory, so it resets when the server restarts. Replacing
`store.py` with SQLite is the natural next step — nothing outside that file
would need to change.
