import json
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request

from configuration import document_from_csv, document_to_csv


def create_app(state) -> Flask:
    template_folder = Path(__file__).with_name("web")
    app = Flask(__name__, template_folder=template_folder)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/config")
    def get_config():
        return jsonify(state.store.load_document())

    @app.put("/api/config")
    def put_config():
        try:
            document = request.get_json(force=True)
            return jsonify(state.apply_document(document))
        except (KeyError, TypeError, ValueError) as error:
            return jsonify({"error": str(error)}), 400

    @app.get("/api/export/json")
    def export_json():
        content = json.dumps(state.store.load_document(), indent=2) + "\n"
        return Response(
            content,
            mimetype="application/json",
            headers={"Content-Disposition": "attachment; filename=devices.json"},
        )

    @app.post("/api/import/json")
    def import_json():
        try:
            uploaded = request.files.get("file")
            document = json.load(uploaded.stream) if uploaded else request.get_json(force=True)
            return jsonify(state.apply_document(document))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            return jsonify({"error": str(error)}), 400

    @app.get("/api/export/csv")
    def export_csv():
        return Response(
            document_to_csv(state.store.load_document()),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=devices.csv"},
        )

    @app.post("/api/import/csv")
    def import_csv():
        try:
            uploaded = request.files.get("file")
            if not uploaded:
                raise ValueError("A CSV file is required")
            document = document_from_csv(uploaded.stream.read().decode("utf-8-sig"))
            return jsonify(state.apply_document(document))
        except (UnicodeDecodeError, KeyError, TypeError, ValueError) as error:
            return jsonify({"error": str(error)}), 400

    return app