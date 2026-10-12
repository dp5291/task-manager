from flask import Blueprint, jsonify, request
from services.tasks import get_task, create_task, process_order, list_tasks, update_task
from services.users import get_user
from utils.errors import AppError, ValidationError

api = Blueprint("api", __name__)

@api.errorhandler(AppError)
def handle_app_error(e):
    return jsonify({"error": e.message}), e.status_code

def _get_json_object() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("body", "must be a JSON object")
    return data

@api.route("/tasks/<int:task_id>", methods=["GET"])
def get_task_route(task_id):
    return jsonify(get_task(task_id))

@api.route("/tasks/<int:task_id>", methods=["PATCH"])
def update_task_route(task_id):
    data = _get_json_object()
    return jsonify(update_task(task_id, data.get("priority")))

@api.route("/tasks", methods=["POST"])
def create_task_route():
    data = _get_json_object()
    extra = {"priority": data["priority"]} if "priority" in data else {}
    return jsonify(create_task(data.get("title"), data.get("user_id"), **extra)), 201

@api.route("/tasks", methods=["GET"])
def list_tasks_route():
    sort = request.args.get("sort")
    if sort is not None and sort != "priority":
        raise ValidationError("sort", "must be priority")
    tasks = list_tasks(request.args.get("priority"))
    if sort == "priority":
        tasks = sorted(tasks, key=lambda task: (task["priority"], task["id"]))
    return jsonify(tasks)

@api.route("/users/<int:user_id>", methods=["GET"])
def get_user_route(user_id):
    return jsonify(get_user(user_id))
