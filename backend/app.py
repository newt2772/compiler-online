import os
from flask import Flask, request, jsonify, render_template
from database import db, log_execution, get_recent, get_saved, toggle_save, delete_entry
from executor import execute
from languages import list_languages

MAX_CODE_LENGTH = 50000
MAX_INPUT_LENGTH = 10000

app = Flask(__name__)

data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(data_dir, exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(data_dir, "history.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/languages", methods=["GET"])
def get_languages():
    return jsonify(list_languages())


@app.route("/api/compile", methods=["POST"])
def compile_code():
    data = request.get_json(silent=True) or {}

    language = data.get("language", "").strip()
    code = (data.get("code") or "")[:MAX_CODE_LENGTH]
    user_input = (data.get("input") or "")[:MAX_INPUT_LENGTH]

    if not code:
        return jsonify({"success": False, "output": "No code provided", "error": ""})
    if not language:
        return jsonify({"success": False, "output": "No language specified", "error": ""})

    result = execute(language, code, user_input)

    log_execution(
        language=language,
        code=code,
        input_text=user_input,
        output=result.get("output", "") + result.get("error", ""),
        success=result.get("success", False),
    )

    return jsonify(result)


@app.route("/api/history/recent", methods=["GET"])
def history_recent():
    entries = get_recent(3)
    return jsonify([e.to_dict() for e in entries])


@app.route("/api/history/saved", methods=["GET"])
def history_saved():
    entries = get_saved()
    return jsonify([e.to_dict() for e in entries])


@app.route("/api/history/<int:entry_id>/save", methods=["POST"])
def history_toggle_save(entry_id):
    entry = toggle_save(entry_id)
    if not entry:
        return jsonify({"success": False, "error": "Entry not found"}), 404
    return jsonify({"success": True, "entry": entry.to_dict()})


@app.route("/api/history/<int:entry_id>", methods=["DELETE"])
def history_delete(entry_id):
    if delete_entry(entry_id):
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Entry not found"}), 404


if __name__ == "__main__":
    from waitress import serve
    print("Online Compiler running at http://0.0.0.0:5000")
    serve(app, host="0.0.0.0", port=5000)
