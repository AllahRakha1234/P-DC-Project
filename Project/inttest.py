from tkinter import filedialog
import sys
import io
import hashlib
import pickle
import socket
import sys
import threading
import time
import tkinter as tk
from request_handler import RequestHandler
# from gui import MainApplication
MAX_BITS = 4
SLEEP_TIME = 5


screen_width = 800
screen_height = 800
scrollable_frame = 0

def get_hash(key):
    result = hashlib.sha256(key.encode())
    return int(result.hexdigest(), 16) % pow(2, MAX_BITS)

class Computer:
    def __init__(self, id, specs):
        self.id = id
        self.specs = specs
        self.file_path = None

class Node:

    def __init__(self, ip, port, listen_param=None):
        '''
        storage:
        '''
        self.ip = ip
        self.port = port
        self.address = (ip, port)
        self.selected_node = None
        
        self.update_nodes = True 
        self.computers_dict = None
        # a nodes identifier is chosen by hashing the nodes IP address - paper
        # we use a combination of ip and port during testing otherwise all nodes will have the same ip
        self.id = get_hash(self.ip + ":" + str(self.port))
        self.finger_table = []
        self.init_finger_table()

        self.pred = None
        self.succ = self.address
        self.pred_id = None
        self.succ_id = self.id
        self.threads = []
        self.run_threads = True

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind((self.ip, self.port))
            if listen_param != None:
                self.socket.listen(listen_param)
            else:
                self.socket.listen()
        except socket.error as msg:
            print('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
            sys.exit()

        self.request_handler = RequestHandler()

    def init_finger_table(self):
        """
        just initializes the finger table to entries pointing to self
        """
        for i in range(MAX_BITS):
            x = pow(2, i)
            entry = (self.id + x) % pow(2, MAX_BITS)
            self.finger_table.append([entry, None])

    def send_file(self, destination, file_path):
        try:
            with open(file_path, 'rb') as file:
                file_content = file.read()
                # print("S",file_content)
                file_content = b'received_file:' + file_content
                # print("S",file_content)
                # print("S",type(file_content))
                serialized_content = pickle.dumps(file_content)
                # print("SS: ",serialized_content)
                response = self.request_handler.send_message(destination, serialized_content)
                if response[0:7] == "output:":
                    print("output: ")
                    print(response[7:])
                    return response[7:]
                else:
                    print("Failed to send file.")
        except FileNotFoundError:
            print("File not found.")
        except Exception as e:
            print("An error occurred:", e)

    def receive_file(self, file_content, file_path):
        try:
            file_content = file_content.encode('utf-8')
            with open(file_path, 'wb') as file:
                file.write(file_content)
            return "success"
        except Exception as e:
            print("An error occurred while receiving the file:", e)
            return "error"

    def start(self):
        """
        Launches all needed threads. It launches the threads and keeps track of them in the threads
        list of the node. Launches a thread for: stabilize, fix fingers, check predecessor, menu and request listener.
        :return:
        """
        self.finger_table[0][1] = self.succ

        t_stab = threading.Thread(target=self.stabilize)
        t_stab.start()
        self.threads.append(t_stab)
        t_fix = threading.Thread(target=self.fix_fingers)
        t_fix.start()
        self.threads.append(t_fix)
        t_check = threading.Thread(target=self.check_predecessor)
        t_check.start()
        self.threads.append(t_check)

        t_menu = threading.Thread(target=self.run)
        t_menu.start()
        self.threads.append(t_menu)

        try:
            while self.run_threads:
                connection, address = self.socket.accept()
                
                th = threading.Thread(target=self.request_listener, args=(connection, address))
                th.start()
                self.threads.append(th)
        except KeyboardInterrupt:
            print("Keyboard interrupt received. Exiting...")
        except OSError as e:
            print("Attempting Exit")
        finally:
            # Cleanup before exiting
            self.socket.close()
            for thread in self.threads:
                thread.join()



    def request_listener(self, connection, address):
        """
        when another node makes a connection with us, a thread is launched that runs this function. It is responsible
        of running the handle request method and sending back the results
        :param connection: The connection object created when we received a request
        :param address: The address of the node that we handle the request for
        :return: The method does not return something back. It just sends back the result with the socket connection
        """

        data = pickle.loads(connection.recv(1024))
        data = self.handle_request(data, connection)
        connection.sendall(pickle.dumps(data))
    
    def handle_request(self, msg, address):
        """
        Responsible for calling the right method depending on the data of the message that was sent as a request
        :param msg: The Message that was sent as a request
        :return: returns the result created when handling the request
        """
        if type(msg) == bytes:
            
            msg = pickle.loads(msg)
            # print("Received message1:", msg)
            try:
                msg = msg.decode('utf-8')  # Try decoding with UTF-8
            except UnicodeDecodeError:
                # Handle non-decodable bytes gracefully
                msg = msg.decode('latin-1')  # Try decoding with Latin-1
            print("Received message2:", msg)
        request = msg.split(":")[0]
        result = ''
        # print("Request:", type(request))
        if request == "join":
            data = msg.split(":")[1:]
            result = self.find_successor(data[2])
            print('result',result)

        if request == "find_successor":
            data = msg.split(":")[1:]
            result = self.find_successor(data[0])

        if request == "get_successor":
            result = {
                "id": self.id,
                "address": self.address,
                "successor_id": self.succ_id,
                "predecessor_id": self.pred_id,
                "succ": self.succ,
                "pred": self.pred
            }

        if request == "find_predecessor":
            data = msg.split(":")[1:]
            result = self.find_predecessor(data[0])

        if request == "get_predecessor":
            result = [self.pred_id, self.pred]

        if request == "notify":
            data = msg.split(":")[1:]
            self.notify(data[0], data[1], data[2])
            result = "notified"

        if request == "ping":
            result = "pinged"

        if request == "received_file":
            code = msg[len("received_file:"):]
            print(code)
            print(type(code))
            output = self.execute_python_code(code)
            print(output)
            result = "output:"+output

        if request == "update_predecessor":
            data = msg.split(":")[1:]
            if len(data) >= 2:
                pred_id = data[0]
                pred_ip, pred_port = eval(data[1])
                self.update_predecessor(pred_id, (pred_ip, pred_port))
                result = "predecessor_updated"
            else:
                result = "error: update_predecessor message format incorrect"

        elif request == "update_successor":
            data = msg.split(":")[1:]
            if len(data) >= 2:
                succ_id = data[0]
                succ_ip, succ_port = eval(data[1])
                self.update_successor(succ_id, (succ_ip, succ_port))
                result = "successor_updated"
            else:
                result = "error: update_successor message format incorrect"

        return result

    def find_successor(self, id):
        """
        Find successor method, follows what was the pseudo code of the paper, just adds more coniditions
        Uses the closes preceding node function.
        :param id: The ID of the node that is trying to join the network
        :return:
        """
        if self.id < int(id) < self.succ_id or self.succ_id == self.id:
            return self.succ
        else:
            finger = self.closest_preceding_node(id)
            if finger == self.address:
                return self.address

            address = self.request_handler.send_message(finger, "find_successor:{}".format(id))
            if address == "error":
                return self.address
            return address

    def closest_preceding_node(self, id):
        """
        Closest preceding node function, same as the paper pseudo code. Goes through the entries in the finger table
        and if one satisfies the condition, returns the entry
        :param id: the id of the node
        :return:
        """
        for finger in reversed(self.finger_table):
            if self.id < finger[0] < int(id):
                return finger[1]
        return self.succ

    def notify(self, pred_id, pred_ip, pred_port):
        """
        Update the nodes own predecessor to the id given by the request.
        :param id:
        :return:
        """
        self.pred = (pred_ip, int(pred_port))
        self.pred_id = int(pred_id)
        print("Notified with predecessor:", self.pred_id)

    def run(self):
        """
        Function that runs in a thread, allowing user input to add nodes
        :return:
        """
        while True:
            time.sleep(2)

    def stabilize(self):
        """
        stabilize method from the pseudo code of the paper. Check the predecessors of the successors.
        :return:
        """
        while True:
            time.sleep(2)
            try:
                if self.succ == self.address:
                    continue
                message = "get_predecessor"
                predecessor = self.request_handler.send_message(self.succ, message)
                if predecessor != 'error':
                    predecessor = eval(predecessor)
                    if predecessor[0] and self.id < predecessor[0] < self.succ_id:
                        self.succ = predecessor[1]
                        self.succ_id = predecessor[0]

                self.request_handler.send_message(self.succ, "notify:{}:{}:{}".format(self.id, self.ip, self.port))
            except Exception as e:
                print(f"Exception in stabilize method: {e}")

    def fix_fingers(self):
        """
        fix_finger method from the pseudo code of the paper
        :return:
        """
        while True:
            time.sleep(2)
            try:
                for i in range(MAX_BITS):
                    entry = (self.id + pow(2, i)) % pow(2, MAX_BITS)
                    self.finger_table[i][0] = entry
                    self.finger_table[i][1] = self.find_successor(entry)
            except Exception as e:
                print(f"Exception in fix_fingers method: {e}")

    def check_predecessor(self):
        """
        check predecessor method from the pseudo code of the paper. Just pings the node's predecessor
        and if the ping fails, sets own predecessor to None
        :return:
        """
        while True:
            time.sleep(2)
            try:
                if self.pred:
                    response = self.request_handler.send_message(self.pred, "ping")
                    if response != "pinged":
                        self.pred = None
            except Exception as e:
                print(f"Exception in check_predecessor method: {e}")

    def update_predecessor(self, pred_id, pred_address):
        self.pred_id = pred_id
        self.pred = pred_address

    def update_successor(self, succ_id, succ_address):
        self.succ_id = succ_id
        self.succ = succ_address

    def execute_python_code(self, code):
        try:
            compiled_code = compile(code, '<string>', 'exec')
            stdout_capture = io.StringIO()
            sys.stdout = stdout_capture
            exec(compiled_code, globals(), locals())
            sys.stdout = sys.__stdout__
            return stdout_capture.getvalue()
        except Exception as e:
            return f"Error executing code: {str(e)}"


class Window(tk.Tk):
    def __init__(self, ip, port):
        super().__init__()

        self.node = Node(ip, port)
        self.node.start()

        self.geometry("800x600")
        self.title("Node Interface")
        self.create_widgets()

    def create_widgets(self):
        # Create the menu bar
        menu_bar = tk.Menu(self)
        self.config(menu=menu_bar)

        # Create a file menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)

        # Add menu items to the file menu
        file_menu.add_command(label="Open File", command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        # Add a Label to display file contents
        self.label = tk.Label(self, text="", wraplength=700)
        self.label.pack(pady=20)

        # Add a leave button
        self.leave_button = tk.Button(self, text="Leave", command=self.leave)
        self.leave_button.pack(side=tk.BOTTOM, pady=20)
        
    def open_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            with open(file_path, 'r') as file:
                content = file.read()
                self.label.config(text=content)
                self.node.send_file(self.node.succ, file_path)

    def leave(self):
        self.node.run_threads = False
        self.node.socket.close()
        self.destroy()

def App(ip, port):
    app = Window(ip, port)
    app.mainloop()

if __name__ == "__main__":
    ip = "127.0.0.1"
    port = 5000
    App(ip, port)
