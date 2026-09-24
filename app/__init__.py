"""Application factory.

Building the app inside a function rather than at import time lets the
tests create a fresh, isolated instance per test run.
"""

from flask import Flask, jsonify, render_template, request

from . import store
from .routes_api import api
from .routes_web import web


def create_app(seed=True):
    app = Flask(__name__)

    store.reset(seed=seed)

    app.register_blueprint(web)
    app.register_blueprint(api)

    @app.errorhandler(404)
    def not_found(error):
        # API callers want JSON; browsers want the styled page.
        if request.path.startswith("/api/"):
            return jsonify({"error": "Not found", "path": request.path}), 404
        return render_template("404.html"), 404

    return app
