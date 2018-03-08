from flask import Flask
from flask_assistant import Assistant, ask, tell
import logging
import socket


TCP_IP = '127.0.0.1'
TCP_PORT = 1315
BUFFER_SIZE = 1024

logging.getLogger('flask_assistant').setLevel(logging.DEBUG)
app = Flask(__name__)
assist = Assistant(app, '/')

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))

@assist.action('greeting')
def greet_and_start():
    speech = "Hi, how can I help you?"
    return ask(speech)


@assist.action("object-to-detect")
def detect_object(object):
    print(object)
    message = handle_detect_object(object)
    return ask(message)

def handle_detect_object(object):
    s.send(object)
    message = s.recv(BUFFER_SIZE)
    return message

@assist.action("unknown-object")
def handle_unknown_object():
    return ask("Sorry, I can only detect bottles right now. Please try a different object.")


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
