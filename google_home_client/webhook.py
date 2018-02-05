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

@assist.action('greeting')
def greet_and_start():
    speech = "Hey what's up hello?"
    return ask(speech)


@assist.action("object-to-detect")
def detect_object(object):
    print(object)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_PORT))
    s.send(object)
    message = s.recv(BUFFER_SIZE)
    # may want to use tell if we want the session to end
    return ask(message)


if __name__ == '__main__':
    app.run(debug=True)
