"""Chat routes — AI coding assistant."""
import json
from flask import (Blueprint, render_template, request, jsonify,
                   Response, stream_with_context, current_app)
from flask_login import login_required, current_user
from app import db
from app.models import ChatMessage
from app.services.ai_service import chat_completion, chat_completion_stream, get_available_models
from app.services.ai_guard import CODELAB_SYSTEM_PROMPT, is_on_topic

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/chat')
@login_required
def chat_page():
    """AI Chat page."""
    models = get_available_models()
    # Load last 50 messages for context
    messages = ChatMessage.query.filter_by(
        user_id=current_user.id
    ).order_by(ChatMessage.created_at.desc()).limit(50).all()
    messages = list(reversed(messages))  # oldest first

    return render_template('chat/index.html', models=models, messages=messages)


@chat_bp.route('/chat/send', methods=['POST'])
@login_required
def send_message():
    """Send a message and get AI response (non-streaming)."""
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Message is required.'}), 400

    user_message = data['message'].strip()
    model = data.get('model', current_app.config.get('DEFAULT_CHAT_MODEL'))
    print("=" * 50)
    print("Received data:", data)
    print("Model selected:", model)
    print("Default model:", current_app.config.get("DEFAULT_CHAT_MODEL"))
    print("=" * 50)

    if not user_message:
        return jsonify({'error': 'Message cannot be empty.'}), 400

    # ── Layer 1: Pre-filter off-topic messages (no API cost) ──
    on_topic, rejection = is_on_topic(user_message)
    if not on_topic:
        # Save both the user message and the rejection as assistant reply
        msg = ChatMessage(user_id=current_user.id, role='user',
                          content=user_message, model=model)
        reject_msg = ChatMessage(user_id=current_user.id, role='assistant',
                                 content=rejection, model=model)
        db.session.add(msg)
        db.session.add(reject_msg)
        db.session.commit()
        return jsonify({'reply': rejection, 'model': model})

    # Save user message
    msg = ChatMessage(
        user_id=current_user.id,
        role='user',
        content=user_message,
        model=model
    )
    db.session.add(msg)

    # Build conversation history (last 20 messages for context)
    history = ChatMessage.query.filter_by(
        user_id=current_user.id
    ).order_by(ChatMessage.created_at.desc()).limit(20).all()
    history = list(reversed(history))

    # ── Layer 2: Hardened system prompt (LLM-side enforcement) ──
    messages = [
        {'role': 'system', 'content': CODELAB_SYSTEM_PROMPT}
    ]
    for h in history:
        messages.append({'role': h.role, 'content': h.content})

    try:
        reply = chat_completion(messages, model=model)
        # Save assistant message
        assistant_msg = ChatMessage(
            user_id=current_user.id,
            role='assistant',
            content=reply,
            model=model
        )
        db.session.add(assistant_msg)
        db.session.commit()

        return jsonify({'reply': reply, 'model': model})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'AI service error: {str(e)}'}), 500


@chat_bp.route('/chat/stream', methods=['POST'])
@login_required
def stream_message():
    """Send a message and get streaming AI response via SSE."""
    print("=" * 50)
    print("Headers:", dict(request.headers))

    data = request.get_json(silent=True)

    print("JSON:", data)

    if not data:
        return jsonify({"error": "No JSON received"}), 400

    print("Model:", data.get("model"))
    print("=" * 50)
    if not data or 'message' not in data:
        return jsonify({'error': 'Message is required.'}), 400

    user_message = data['message'].strip()
    model = data.get('model', current_app.config.get('DEFAULT_CHAT_MODEL'))

    if not user_message:
        return jsonify({'error': 'Message cannot be empty.'}), 400

    # ── Layer 1: Pre-filter off-topic messages (no API cost) ──
    on_topic, rejection = is_on_topic(user_message)
    if not on_topic:
        msg = ChatMessage(user_id=current_user.id, role='user',
                          content=user_message, model=model)
        reject_msg = ChatMessage(user_id=current_user.id, role='assistant',
                                 content=rejection, model=model)
        db.session.add(msg)
        db.session.add(reject_msg)
        db.session.commit()
        # Return rejection as a single SSE event
        def reject_stream():
            yield f"data: {json.dumps({'chunk': rejection})}\n\n"
            yield f"data: {json.dumps({'done': True, 'model': model})}\n\n"
        return Response(
            stream_with_context(reject_stream()),
            mimetype='text/event-stream',
            headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
        )

    # Save user message
    msg = ChatMessage(
        user_id=current_user.id,
        role='user',
        content=user_message,
        model=model
    )
    db.session.add(msg)

    # Build conversation history
    history = ChatMessage.query.filter_by(
        user_id=current_user.id
    ).order_by(ChatMessage.created_at.desc()).limit(20).all()
    history = list(reversed(history))

    # ── Layer 2: Hardened system prompt (LLM-side enforcement) ──
    messages = [
        {'role': 'system', 'content': CODELAB_SYSTEM_PROMPT}
    ]
    for h in history:
        messages.append({'role': h.role, 'content': h.content})

    def generate():
        full_reply = ''
        try:
            stream = chat_completion_stream(messages, model=model)
            for chunk in stream:
                full_reply += chunk
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"

            # Save full assistant reply
            assistant_msg = ChatMessage(
                user_id=current_user.id,
                role='assistant',
                content=full_reply,
                model=model
            )
            db.session.add(assistant_msg)
            db.session.commit()
            yield f"data: {json.dumps({'done': True, 'model': model})}\n\n"

        except Exception as e:
            db.session.rollback()
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }
    )


@chat_bp.route('/chat/clear', methods=['POST'])
@login_required
def clear_chat():
    """Clear all chat messages for the current user."""
    ChatMessage.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({'success': True})