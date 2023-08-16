from flask_chat_server import socketio
from flask_socketio import send, emit
from flask import request


@socketio.on("connect")
def handle_connect():
    print("Client connected!")
    socketio.emit("connect_completed", request.sid)


# @socketio.on("site_chat")
# def handle_message(message):
#     print(message)
#     for reply in ask_gpt_simple_question(message):
#         socketio.emit("site_chat_reply", reply)


@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected")
