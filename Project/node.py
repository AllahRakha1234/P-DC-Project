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
        self.leach = None
        
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

    def execute_python_code(self, code):
        print("execute_python_code: ", code)
        try:
            # Redirect stdout to a StringIO object to capture the output
            stdout = io.StringIO()
            sys.stdout = stdout

            # Execute the code
            exec(code)

            # Get the captured output
            output = stdout.getvalue()
            return output
        except Exception as e:
            # Return the error message if code execution fails
            return str(e)
        finally:
            # Restore sys.stdout to its original value
            sys.stdout = sys.__stdout__

    # def start(self):
    #     """
    #     Launches all needed threads. It launches the threads and keeps track of them in the threads
    #     list of the node. Launches a thread for: stabilize, fix fingers, check predecessor, menu and request listener.
    #     :return:
    #     """
    #     self.finger_table[0][1] = self.succ

    #     t_stab = threading.Thread(target=self.stabilize)
    #     t_stab.start()
    #     self.threads.append(t_stab)
    #     t_fix = threading.Thread(target=self.fix_fingers)
    #     t_fix.start()
    #     self.threads.append(t_fix)
    #     t_check = threading.Thread(target=self.check_predecessor)
    #     t_check.start()
    #     self.threads.append(t_check)

    #     t_menu = threading.Thread(target=self.menu)
    #     t_menu.start()
    #     self.threads.append(t_menu)

    #     while self.run_threads:
    #         connection, address = self.socket.accept()
            
    #         th = threading.Thread(target=self.request_listener, args=(connection, address))
    #         th.start()
    #         self.threads.append(th)

    #     # t_file = threading.Thread(target=self.handle_file_request, args=(connection, address))
    #     # t_file.start()

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
        data = self.handle_request(data, address)
        connection.sendall(pickle.dumps(data))
    def find_node_by_id(self, node_list, target_id):
        for node in node_list:
            if node['id'] == target_id:
                return node
        return None
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
       
        if request == "join":
            data = msg.split(":")[1:]
            result = self.find_successor(data[2])
            print('result',result)

        elif request == "find_successor":
            data = msg.split(":")[1:]
            result = self.find_successor(data[0])

        elif request == "get_successor":
            result = {
                "id": self.id,
                "address": self.address,
                "successor_id": self.succ_id,
                "predecessor_id": self.pred_id,
                "succ": self.succ,
                "pred": self.pred
            }

        elif request == "find_predecessor":
            data = msg.split(":")[1:]
            result = self.find_predecessor(data[0])

        elif request == "get_predecessor":
            result = [self.pred_id, self.pred]

        elif request == "notify":
            data = msg.split(":")[1:]
            self.notify(data[0], data[1], data[2])
            result = "notified"

        elif request == "ping":
            result = "pinged"

        elif request == "received_file":
            code = msg[len("received_file:"):]
            print(code)
            print(type(code))
            output = self.execute_python_code(code)
            print(output)
            result = "output:"+output

        elif request == "leaving":
            print("SUCCS: ", msg)
            next_id = msg.split(":")[1]
            print("next_id: ",next_id)
            next_node = self.find_node_by_id(self.computers_dict,eval(next_id))
            self.selected_node = next_node
            print(self.selected_node)
            self.request_handler.send_message(self.selected_node["address"], "Selected:{}:{}".format(self.id, self.address))

            # self.selected_node = 

        elif request == "update_predecessor":
            print("update_predecessor")
            data = msg.split(":")[1:]
            if len(data) >= 2:
                pred_id = data[0]
                pred_ip, pred_port = eval(data[1])
                self.update_predecessor(pred_id, (pred_ip, pred_port))
                result = "predecessor_updated"
            else:
                result = "error: update_predecessor message format incorrect"

        elif request == "update_successor":
            print("successor_updated")
            data = msg.split(":")[1:]
            if len(data) >= 2:
                succ_id = data[0]
                succ_ip, succ_port = eval(data[1])
                self.update_successor(succ_id, (succ_ip, succ_port))
                result = "successor_updated"
            else:
                result = "error: update_successor message format incorrect"

        elif request == "Selected":
            print("kk; ",msg.split(":")[2])
            self.leach = eval(msg.split(":")[2])

        else:
            print("IDK: ", msg)
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
        and if one satisfies the condition, returns the address
        :param id: ID of the node trying to join
        :return: Address of the finger table entry that satisfies the requirement
        """
        for i in range(MAX_BITS - 1, 0, -1):
            if self.finger_table[i][1] is not None and self.id < self.finger_table[i][0] < int(id):
                return self.finger_table[i][1]
        return self.address

    def find_predecessor(self, id):
        """
        Find predecessor method
        :param id:
        :return:
        """
        if id == self.id:
            return self.address
        else:
            node_prime = self.closest_preceding_node(id)
            if node_prime == self.address:
                return self.address
            data = self.request_handler.send_message((node_prime), "find_predecessor:{}".format(self.id))
            if data == "error":
                return self.address
            return data

    def join(self, address):
        """
        Join method. When a node wants to join a network, this method is called. It makes a request to the given address
        to receive what should be the node's successor. If the request fails, it prints the error message
        :param address: The known address of the network that we want to join
        :return: Does not return something
        """
        succ = self.request_handler.send_message(address,
                                                 "join:{}:{}:{}".format(self.id, self.ip, self.port))

        if succ == "error":
            print()
            print("===============================================")
            print("=============== UNABLE TO JOIN ================")
            print("=== COULD NOT CONNECT TO THE IP/PORT GIVEN ====")
            print("===============================================")
            print()
            return

        self.succ = succ
        self.succ_id = get_hash(succ[0] + ":" + str(succ[1]))
        print("Node {} successfully joined the Chord ring".format(self.id))

    def notify(self, id, ip, port):
        """
        Recevies notification from stabilize function when there is change in successor. Based on the condition, it will
        change the predessor to the ip and port number given
        :param id: The id
        :param ip: IP of predecessor
        :param port: Port number of predecessor
        :return: Empty
        """
        if self.pred is None or self.pred == self.address or int(self.pred_id) < int(id) < int(self.id) or \
                (int(self.pred_id) > int(self.id) > int(id)) or (int(self.pred_id) < int(id) and int(self.id) < int(id)):
            self.pred = (ip, int(port))
            self.pred_id = get_hash(ip + ":" + port)

    def fix_fingers(self):
        while self.run_threads:
            for i in range(1, MAX_BITS):
                data = self.find_successor(self.finger_table[i][0])
                self.finger_table[i][1] = data
                time.sleep(SLEEP_TIME)

    def stabilize(self):
        while self.run_threads:
            if self.succ is None:
                time.sleep(SLEEP_TIME)
                continue
            result = self.request_handler.send_message(self.succ, "get_predecessor")

            if result == "error":
                self.succ_id = self.id
                self.succ = self.address
            elif result[0] is not None:
                id = get_hash(result[1][0] + ":" + str(result[1][1]))
                if int(self.id) < int(id) < int(self.succ_id) or int(self.succ_id) == int(self.id) or \
                        (int(self.succ_id) < int(self.id) and int(self.succ_id > int(id))) or \
                        (self.succ_id < int(id) and self.id < int(id)):
                    self.succ_id = id
                    self.succ = (result[1][0], result[1][1])
            self.request_handler.send_message(self.succ, "notify:{}:{}:{}".format(self.id, self.ip, self.port))
            time.sleep(SLEEP_TIME)

    def check_predecessor(self):
        while self.run_threads:
            time.sleep(SLEEP_TIME)
            if self.pred is None or self.pred == self.address:
                continue
            ping_result = self.request_handler.send_message(self.pred, "ping")
            if ping_result == "pinged":
                continue
            self.pred = None
            self.pred_id = None

    def leave(self):
        x = self.request_handler.send_message(self.leach, "leaving:{}:{}".format(self.succ_id, self.succ))
        
        # Notify successor to update its predecessor
        self.request_handler.send_message(self.succ, "update_predecessor:{}:{}".format(self.pred_id, self.pred))

        # Notify predecessor to update its successor
        self.request_handler.send_message(self.pred, "update_successor:{}:{}".format(self.succ_id, self.succ))

        print("leach leach: ",self.leach)

        

        # Optionally, transfer data to the successor

        # Stop all threads and close the socket
        self.run_threads = False
        self.socket.close()
        exit(0)

    def update_predecessor(self, pred_id, pred):
        self.pred_id = int(pred_id)
        self.pred = pred

    def update_successor(self, succ_id, succ):
        self.succ_id = int(succ_id)
        self.succ = succ

    # def menu(self):
    #     '''
    #     responsible for the menu of the client
    #     called by the start_node function
    #     :return:
    #     '''
    #     while self.run_threads:
    #         self.print_menu()
    #         mode = input()
    #         if mode == '1':
    #             self.print_finger_table()
    #             pass
    #         elif mode == '2':
    #             self.print_predecessor()
    #         elif mode == '3':
    #             self.print_successor()
    #         elif mode == '4':
    #             all_nodes = self.list_nodes()
    #             print("Nodes in the network:")
    #             for node_info in all_nodes:
    #                 print("ID:", node_info["id"])
    #                 print("Address:", node_info["address"])
    #                 print("Successor ID:", node_info["successor_id"])
    #                 print("Predecessor ID:", node_info["predecessor_id"])
    #                 print()
    #         elif mode == '5':
    #             print("Enter the IP address and port number of the destination node:")
    #             # dest_ip = input("IP: ")
    #             dest_port = int(input("Port: "))
    #             self.send_file(("127.0.0.1", dest_port), 'ne.txt')
    #         elif mode == '6':
    #             print("Leaving...")
    #             self.leave()
                
    #         pass

    def App(self, root):
        self.root = root
        self.root.title(f"Device {self.id} Connected in Chord")
        self.root.configure(bg="#1e1e1e")  # Dark background color
        self.root.attributes('-fullscreen', True)  # Open in full-screen mode

        # Get screen dimensions
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        # Add heading
        heading_label = tk.Label(self.root, text=f"Device {self.id} Connected in Chord", bg="#1e1e1e", font=("Helvetica", 16, "bold"), fg="#FF0000")  # Red color
        heading_label.pack(pady=int(self.screen_height * 0.02))

        # Create a frame for the scrollbar
        self.main_frame = tk.Frame(self.root, bg="#1e1e1e")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.main_frame, bg="#1e1e1e")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = tk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.scrollable_frame = tk.Frame(self.canvas, bg="#1e1e1e")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Dictionary to store IDs and specifications
        self.computer_frames = {}
        self.specs_textboxes = {}
        self.file_labels = {}
        self.select_send_buttons = {}
        self.select = 0
        self.create_computer_entries()

        # Add leave button
        leave_button = tk.Button(self.root, text="Leave", command=self.leave, bg="#FF0000", fg="white", font=("Helvetica", 12, "bold"))
        leave_button.place(x=self.screen_width - 100, y=20)  # Position it at the top-right corner

    def create_computer_entries(self):
        if not self.update_nodes:  # Check if updates are disabled
            return
        
        if self.select == 0:
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()

        row_frame = None
        self.computers_dict = self.list_nodes()
        # print("xxxxxxxxxxx: ")
        for i in range(len(self.computers_dict)):
            device = self.computers_dict[i]
            id = device["id"]
            specs = device
            if i % 3 == 0:
                row_frame = tk.Frame(self.scrollable_frame, bg="#1e1e1e")
                row_frame.pack(pady=int(self.screen_height * 0.02), fill=tk.X)
                # Center the row frame
                self.scrollable_frame.update_idletasks()
                row_frame_width = min(3, len(self.computers_dict) - i) * int(self.screen_width * 0.25) + (min(3, len(self.computers_dict) - i) - 1) * int(self.screen_width * 0.03)  # Width of each computer frame plus padding
                padding_x = max(0, (self.screen_width - row_frame_width) // 2)
                row_frame.pack(padx=padding_x)
            self.add_computer_entry(row_frame, id, specs)
        
        if self.select == 0:
            self.root.after(5000, lambda: self.create_computer_entries())


    def add_computer_entry(self, parent, id, specs):
        computer_frame = tk.Frame(parent, bg="#1e1e1e", padx=int(self.screen_width * 0.01), pady=int(self.screen_height * 0.01))
        computer_frame.pack(pady=int(self.screen_height * 0.02), side=tk.LEFT, padx=int(self.screen_width * 0.03))  # Align frames next to each other with margins

        id_label = tk.Label(computer_frame, text=f"ID: {id}", bg="#1e1e1e", font=("Helvetica", 12, "bold"), fg="#FF0000")  # Red color
        id_label.pack()

        # Add heading to specs textbox
        specs_heading_label = tk.Label(computer_frame, text="Specifications", bg="#1e1e1e", font=("Helvetica", 10, "bold"), fg="#FF0000")  # Red color
        specs_heading_label.pack()

        specs_textbox = tk.Text(computer_frame, height=10, width=40, bg="#2e2e2e", fg="white", font=("Helvetica", 10))  # Darker color
        specs_textbox.insert("1.0", specs)
        specs_textbox.pack()

        connect_button = tk.Button(computer_frame, text="Connect", command=lambda i=(id,specs): self.connect_computer(i), bg="#FF0000", fg="white", font=("Helvetica", 10, "bold"))  # Red color
        connect_button.pack(pady=int(self.screen_height * 0.01))

        self.computer_frames[id] = computer_frame
        self.specs_textboxes[id] = specs_textbox

    def connect_computer(self, node):

        self.request_handler.send_message(node[1]["address"], "Selected:{}:{}".format(self.id, self.address))
        id = node[0]
        self.select = 1
        self.update_nodes = False  # Stop further updates
        for cid, frame in self.computer_frames.items():
            if cid != id:
                frame.pack_forget()  # Hide other frames
            else:
                frame.pack_forget()
                frame.pack(pady=int(self.screen_height * 0.02), side=tk.TOP, fill=tk.BOTH, expand=True)  # Move the selected frame to the middle
                print("id: ",node[1])
                self.selected_node = node[1]
                print("self.selected_node ", self.selected_node )

        frame = self.computer_frames[id]
        for widget in frame.winfo_children():
            if isinstance(widget, tk.Button) and widget.cget("text") == "Connect":
                widget.pack_forget()  # Remove the "Connect" button

        select_send_button = tk.Button(frame, text="Select File", command=lambda: self.select_file(id), bg="#FF0000", fg="white", font=("Helvetica", 10, "bold"))  # Red color
        select_send_button.pack(pady=int(self.screen_height * 0.01))
        self.select_send_buttons[id] = select_send_button


    def select_file(self, id):
        file_path = filedialog.askopenfilename(filetypes=[("Python files", "*.py")])
        if file_path:
            computer = Computer(id, self.specs_textboxes[id].get("1.0", "end-1c").strip())
            computer.file_path = file_path
            # print(f"Selected file for Computer {computer.id}: {file_path}")
            self.update_to_send_file(id, computer)

    def update_to_send_file(self, id, computer):
        frame = self.computer_frames[id]

        # Display the file name above the send file button
        if id in self.file_labels:
            self.file_labels[id].config(text=f"File: {computer.file_path}")
        else:
            file_label = tk.Label(frame, text=f"File: {computer.file_path}", bg="#1e1e1e", font=("Helvetica", 10), fg="white")
            file_label.pack(after=self.specs_textboxes[id])
            self.file_labels[id] = file_label

        select_send_button = self.select_send_buttons[id]
        select_send_button.config(text="Send File", command=lambda: self.send_file1(computer, frame))

    def send_file1(self, computer, frame):
        if computer.file_path:
            # print(f"Sending file for Computer {computer.id}: {computer.file_path}")
            # Implement your logic to send the file here

            # Display output textbox with heading
            output_heading = tk.Label(frame, text="Output", bg="#1e1e1e", font=("Helvetica", 10, "bold"), fg="#FF0000")
            output_heading.pack()

            output = self.send_file(self.selected_node["address"],computer.file_path)

            output_textbox = tk.Text(frame, height=10, width=60, bg="#2e2e2e", fg="white", font=("Helvetica", 10))
            output_textbox.insert("1.0", f"Output for Computer {computer.id} after sending file.\n{output}")
            output_textbox.pack(pady=int(self.screen_height * 0.01))

            # Update the button back to "Select File"
            select_send_button = self.select_send_buttons[computer.id]
            select_send_button.config(text="Select File", command=lambda: self.select_file(computer.id))
    def run(self):
        root = tk.Tk()
        app = self.App(root)
        root.mainloop()
    

    def print_menu(self):
        print("Node ID: {}".format(self.id))
        print("===============================================")
        print("==================  Menu  =====================")
        print("===============================================")
        print("""\n1. Print Finger Table
                 \n2. Print Predecessor
                 \n3. Print Successor
                 \n4. All Nodes
                 \n5. Send File
                 \n6. Leave""")

    def print_predecessor(self):
        print("Predecessor:", self.pred_id)

    def print_successor(self):
        print("Successor:", self.succ_id)

    def print_finger_table(self):
        for key, value in self.finger_table:
            print("KeyID:", key, "Value", value)

    def is_id_in_list(self, new_id, nodes_info):
        for node_info in nodes_info:
            # print(new_id["id"]," ", node_info["address"])
            if node_info["id"] == new_id["id"]:
                # print("yes")
                return True
        return False

    def list_nodes(self):
        """
        Lists all the nodes available in the network by traversing the Chord ring
        starting from the current node.
        """

        # List to store information about each node
        nodes_info = []

        current_node = {
                "id": self.id,
                "address": self.address,
                "successor_id": self.succ_id,
                "predecessor_id": self.pred_id,
                "succ": self.succ,
                "pred": self.pred
            }

        # Traverse the ring
        while True:
            # Append information about the current node
            if ((self.is_id_in_list(current_node,nodes_info))== False):
                nodes_info.append(current_node)

            # Move to the successor node
            current_node = self.request_handler.send_message(current_node["succ"], "get_successor")
            # print(current_node)

            # Break the loop if we've completed a full circle
            if current_node["id"] == self.id:
                break

        return nodes_info

    



if __name__ == '__main__':

    # create chord ring
    if len(sys.argv) == 3:
        ip = sys.argv[1]
        port = int(sys.argv[2])

        node = Node(ip, port)
        print("Node launched with ID:", node.id)
        node.start()

    elif len(sys.argv) == 5:
        known_ip = sys.argv[1]
        known_port = int(sys.argv[2])

        ip = sys.argv[3]
        port = int(sys.argv[4])

        node = Node(ip, port)
        node.join((known_ip, known_port))
        print("Node launched with ID:", node.id)
        node.start()
        
    else:
        print()
        print("Not enough arguments given")
        print("Usage: python node.py <ip> <port>")
        print()
        print("Now Exiting ------------>")
        print("Goodbye")
        exit()