from flask import Blueprint, jsonify, request
from services.tasks import get_task, create_task, process_order, update_task, list_tasks
from services.users import get_user, list_users, get_notification_pref, set_notification_pref
from services.tags import create_tag
from utils.errors import AppError

api = Blueprint("api", __name__)

@api.errorhandler(AppError)
def handle_app_error(e):
    return jsonify({"error": e.message}), e.status_code

@api.route("/tasks", methods=["GET"])
def list_tasks_route():
    return jsonify(list_tasks(request.args.get("priority")))

@api.route("/tasks/<int:task_id>", methods=["GET"])
def get_task_route(task_id):
    return jsonify(get_task(task_id))

@api.route("/tasks", methods=["POST"])
def create_task_route():
    data = request.get_json()
    return jsonify(create_task(data["title"], data["user_id"], priority=data.get("priority", 3))), 201

@api.route("/tasks/<int:task_id>", methods=["PATCH"])
def update_task_route(task_id):
    data = request.get_json()
    return jsonify(update_task(task_id, data))

@api.route("/users/<int:user_id>", methods=["GET"])
def get_user_route(user_id):
    return jsonify(get_user(user_id))

@api.route("/users", methods=["GET"])
def list_users_route():
    return jsonify(list_users())

@api.route("/users/<int:user_id>/notifications", methods=["GET"])
def get_notification_pref_route(user_id):
    return jsonify({"user_id": user_id, "notification_pref": get_notification_pref(user_id)})

@api.route("/users/<int:user_id>/notifications", methods=["PATCH"])
def set_notification_pref_route(user_id):
    data = request.get_json()
    set_notification_pref(user_id, data["notification_pref"])
    return jsonify({"user_id": user_id, "notification_pref": get_notification_pref(user_id)})

@api.route("/tags", methods=["POST"])
def create_tag_route():
    data = request.get_json()
    return jsonify(create_tag(data)), 201
