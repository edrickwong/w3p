import socket

TCP_IP = '127.0.0.1'
TCP_PORT = 1315
BUFFER_SIZE = 1024

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))

while True:
    try:
        message = raw_input("What do you want to say: ")
        s.send(message)
        reply = s.recv(BUFFER_SIZE)
        print reply
    except KeyboardInterrupt:
        break

s.close()
