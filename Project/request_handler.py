import socket, pickle

class RequestHandler:
    
    def __init__(self):
        pass
    
    def send_message(self, address, message):
        try:
            ping = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # connect to server on local computer
            ping.connect(address)
            ping.send(pickle.dumps(message))
            data = pickle.loads(ping.recv(1024))
            ping.close()
            return data
        except socket.error:
            # print("NO CONNECTION")
            return "error"
        except:
            return "error"
