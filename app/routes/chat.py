from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.services.chatbot_logic import route_message

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')


@chat_bp.route('/')
@login_required
def chat_page():
    """Render the chat UI."""
    return render_template('chat.html')


@chat_bp.route('/message', methods=['POST'])
@login_required
def chat_message():
    """
    JSON API endpoint consumed by the frontend via fetch().
    Body: { "message": "..." }
    Returns: { "intent": "...", "reply": "...", "data": {...} }
    """
    body = request.get_json(silent=True) or {}
    user_message = (body.get('message') or '').strip()

    if not user_message:
        return jsonify({"intent": "UNKNOWN", "reply": "Please type a message.", "data": None}), 400

    response = route_message(user_message, current_user)
    return jsonify(response)
