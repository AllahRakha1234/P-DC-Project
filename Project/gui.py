import tkinter as tk
from tkinter import filedialog

# Create textboxes for each ID and specification
computer_frames = {}
specs_textboxes = {}
file_labels = {}
select_send_buttons = {}

class Computer:
    def __init__(self, id, specs):
        id = id
        specs = specs
        file_path = None

screen_width = 800
screen_height = 800
scrollable_frame = 0
# class MainApplication:

def App( root):
    root = root
    root.title("Devices Connected in Chord")
    root.configure(bg="#1e1e1e")  # Dark background color
    root.attributes('-fullscreen', True)  # Open in full-screen mode

    # Get screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Add heading
    heading_label = tk.Label(root, text="Devices Connected in Chord", bg="#1e1e1e", font=("Helvetica", 16, "bold"), fg="#FF0000")  # Red color
    heading_label.pack(pady=int(screen_height * 0.02))

    # Create a frame for the scrollbar
    main_frame = tk.Frame(root, bg="#1e1e1e")
    main_frame.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(main_frame, bg="#1e1e1e")
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    scrollable_frame = tk.Frame(canvas, bg="#1e1e1e")

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

# Dictionary to store IDs and specifications
computers_dict = {
    "1": "Specs for ID 1",
    "2": "Specs for ID 2",
    "3": "Specs for ID 3",
    "4": "Specs for ID 4",
    "5": "Specs for ID 5",
    "6": "Specs for ID 6",
    "7": "Specs for ID 7",
    "8": "Specs for ID 8",
    "9": "Specs for ID 9",
    "10": "Specs for ID 10",
    "11": "Specs for ID 11",
    "12": "Specs for ID 12"
}

def send_file(computer, frame):
    if computer.file_path:
        print(f"Sending file for Computer {computer.id}: {computer.file_path}")
        # Implement your logic to send the file here

        # Display output textbox with heading
        output_heading = tk.Label(frame, text="Output", bg="#1e1e1e", font=("Helvetica", 10, "bold"), fg="#FF0000")
        output_heading.pack()

        output_textbox = tk.Text(frame, height=10, width=60, bg="#2e2e2e", fg="white", font=("Helvetica", 10))
        output_textbox.insert("1.0", f"Output for Computer {computer.id} after sending file.")
        output_textbox.pack(pady=int(screen_height * 0.01))

        # Update the button back to "Select File"
        select_send_button = select_send_buttons[computer.id]
        select_send_button.config(text="Select File", command=lambda: select_file(computer.id))


def update_to_send_file(id, computer):
    frame = computer_frames[id]

    # Display the file name above the send file button
    if id in file_labels:
        file_labels[id].config(text=f"File: {computer.file_path}")
    else:
        file_label = tk.Label(frame, text=f"File: {computer.file_path}", bg="#1e1e1e", font=("Helvetica", 10), fg="white")
        file_label.pack(after=specs_textboxes[id])
        file_labels[id] = file_label

    select_send_button = select_send_buttons[id]
    select_send_button.config(text="Send File", command=lambda: send_file(computer, frame))


def select_file(id):
    file_path = filedialog.askopenfilename(filetypes=[("Python files", "*.py")])
    if file_path:
        computer = Computer(id, specs_textboxes[id].get("1.0", "end-1c").strip())
        computer.file_path = file_path
        print(f"Selected file for Computer {computer.id}: {file_path}")
        update_to_send_file(id, computer)


def connect_computer(id):
    for cid, frame in computer_frames.items():
        if cid != id:
            frame.pack_forget()  # Hide other frames
        else:
            frame.pack_forget()
            frame.pack(pady=int(screen_height * 0.02), side=tk.TOP, fill=tk.BOTH, expand=True)  # Move the selected frame to the middle

    frame = computer_frames[id]
    for widget in frame.winfo_children():
        if isinstance(widget, tk.Button) and widget.cget("text") == "Connect":
            widget.pack_forget()  # Remove the "Connect" button

    select_send_button = tk.Button(frame, text="Select File", command=lambda: select_file(id), bg="#FF0000", fg="white", font=("Helvetica", 10, "bold"))  # Red color
    select_send_button.pack(pady=int(screen_height * 0.01))
    select_send_buttons[id] = select_send_button


def add_computer_entry(parent, id, specs):
    computer_frame = tk.Frame(parent, bg="#1e1e1e", padx=int(screen_width * 0.01), pady=int(screen_height * 0.01))
    computer_frame.pack(pady=int(screen_height * 0.02), side=tk.LEFT, padx=int(screen_width * 0.03))  # Align frames next to each other with margins

    id_label = tk.Label(computer_frame, text=f"ID: {id}", bg="#1e1e1e", font=("Helvetica", 12, "bold"), fg="#FF0000")  # Red color
    id_label.pack()

    # Add heading to specs textbox
    specs_heading_label = tk.Label(computer_frame, text="Specifications", bg="#1e1e1e", font=("Helvetica", 10, "bold"), fg="#FF0000")  # Red color
    specs_heading_label.pack()

    specs_textbox = tk.Text(computer_frame, height=10, width=40, bg="#2e2e2e", fg="white", font=("Helvetica", 10))  # Darker color
    specs_textbox.insert("1.0", specs)
    specs_textbox.pack()

    connect_button = tk.Button(computer_frame, text="Connect", command=lambda i=id: connect_computer(i), bg="#FF0000", fg="white", font=("Helvetica", 10, "bold"))  # Red color
    connect_button.pack(pady=int(screen_height * 0.01))

    computer_frames[id] = computer_frame
    specs_textboxes[id] = specs_textbox


def create_computer_entries():
    row_frame = None
    for i, (id, specs) in enumerate(computers_dict.items()):
        if i % 3 == 0:
            row_frame = tk.Frame(scrollable_frame, bg="#1e1e1e")
            row_frame.pack(pady=int(screen_height * 0.02), fill=tk.X)
            # Center the row frame
            scrollable_frame.update_idletasks()
            row_frame_width = min(3, len(computers_dict) - i) * int(screen_width * 0.25) + (min(3, len(computers_dict) - i) - 1) * int(screen_width * 0.03)  # Width of each computer frame plus padding
            padding_x = max(0, (screen_width - row_frame_width) // 2)
            row_frame.pack(padx=padding_x)

        add_computer_entry(row_frame, id, specs)

create_computer_entries()






if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
