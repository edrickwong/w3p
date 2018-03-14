from flask import Flask
from flask_assistant import Assistant, ask, tell
import logging
import socket


TCP_IP = '127.0.0.1'
TCP_PORT = 1315
BUFFER_SIZE = 1024

# Fixed responses
GREETING = "Hi, how can I help you?"
UNKNOWN_OBJ_RESP = "Sorry, I can only detect bottles right now. Please try a different object."

logging.getLogger('flask_assistant').setLevel(logging.DEBUG)
app = Flask(__name__)
assist = Assistant(app, '/')

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))

# keeps track of last message said by Google Home
msg_stack = []

def respond(msg):
    msg_stack.append(msg)
    return ask(msg)

@assist.action('greeting')
def greet_and_start():
    return respond(GREETING)

@assist.action("object-to-detect")
def detect_object(object):
    message = handle_detect_object(object)
    return respond(message)

def handle_detect_object(object):
    s.send(object)
    message = s.recv(BUFFER_SIZE)
    return message

@assist.action("unknown-object")
def handle_unknown_object():
    return respond(UNKNOWN_OBJ_RESP)

@assist.action("repeat")
def repeat():
    most_recent_msg = msg_stack[-1:][0]
    return respond(most_recent_msg)


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
