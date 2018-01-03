import socket

TCP_IP = '127.0.0.1'
TCP_PORT = 1315
BUFFER_SIZE = 1024

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)

conn, addr = s.accept()
print 'Conn address: %s' %(str(addr))

while True:
    try:
        data = conn.recv(BUFFER_SIZE)
        if data:
            print "recieved: %s" %(data)
        else:
            print "no data"
            continue
    except KeyboardInterrupt:
        print "Exiting"
        break
conn.close()
