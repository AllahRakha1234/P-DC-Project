import subprocess
import platform,time

# Define the commands
cmd1 = ['python', 'node.py', '127.0.0.1', '5000']
cmd2 = ['python', 'node.py', '127.0.0.1', '5000', '127.0.0.1', '5001']
cmd3 = ['python', 'node.py', '127.0.0.1', '5000', '127.0.0.1', '5002']


# Function to open a new terminal and run a command
def open_terminal_and_run(command):
    system = platform.system()
    
    if system == 'Windows':
        # For Windows, use 'start' to open a new terminal
        subprocess.Popen(['start', 'cmd', '/k'] + command, shell=True)
    elif system == 'Darwin':  # macOS
        # For macOS, use 'osascript' to open a new terminal
        subprocess.Popen(['osascript', '-e', f'tell application "Terminal" to do script "{" ".join(command)}"'])
    elif system == 'Linux':
        # For Linux, use 'gnome-terminal' or 'xterm' to open a new terminal
        try:
            subprocess.Popen(['gnome-terminal', '--'] + command)
        except FileNotFoundError:
            subprocess.Popen(['xterm', '-hold', '-e'] + command)
    else:
        raise OSError(f"Unsupported operating system: {system}")

# Open two terminals and run the commands
open_terminal_and_run(cmd1)
time.sleep(6)
open_terminal_and_run(cmd2)
time.sleep(6)
open_terminal_and_run(cmd3)

