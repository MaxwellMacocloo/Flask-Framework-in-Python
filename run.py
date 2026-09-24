"""Development server entry point.

    python run.py

The factory lives in app/__init__.py; this file only wires it to the
built-in dev server.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
