import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import sys
import os
import shlex
import subprocess

IS_POSIX = os.name == "posix"

# History
MAX_HISTORY = 50
history = []

#  History functions 
def append_history(command):
    if not command.strip():
        return
    history.append(command)
    if len(history) > MAX_HISTORY:
        history.pop(0)

def display_history():
    for i, cmd in enumerate(history, start=1):
        print(f"[{i}] {cmd}", end="")

#  Run commands 
def run_command(command_string):
    try:
        tokens = shlex.split(command_string)
    except ValueError:
        return ""

    if not tokens:
        return ""

    #  Built-ins 
    if tokens[0] == "cd":
        if len(tokens) < 2:
            return "cd: expected argument\n"
        try:
            os.chdir(tokens[1])
        except OSError as e:
            return f"cd failed: {e}\n"
        return ""

    if tokens[0] == "history":
        output = ""
        for i, cmd in enumerate(history, start=1):
            output += f"[{i}] {cmd}"
        return output

    #  Output redirection 
    redirect_file = None
    if ">" in tokens:
        idx = tokens.index(">")
        if idx + 1 >= len(tokens):
            return "No file specified for redirection\n"
        redirect_file = tokens[idx + 1]
        tokens = tokens[:idx]

    #  Pipe handling 
    if "|" in tokens:
        pipe_index = tokens.index("|")
        left_cmd = tokens[:pipe_index]
        right_cmd = tokens[pipe_index + 1:]
        try:
            if IS_POSIX:
                p1 = subprocess.Popen(left_cmd, stdout=subprocess.PIPE, text=True)
                p2 = subprocess.Popen(right_cmd, stdin=p1.stdout, stdout=subprocess.PIPE, text=True)
            else:
                p1 = subprocess.Popen(["cmd", "/c"] + left_cmd, stdout=subprocess.PIPE, text=True)
                p2 = subprocess.Popen(["cmd", "/c"] + right_cmd, stdin=p1.stdout, stdout=subprocess.PIPE, text=True)
            p1.stdout.close()
            output, _ = p2.communicate()
            return output
        except FileNotFoundError:
            return "Command not found\n"

    #  Normal execution 
    try:
        if redirect_file:
            with open(redirect_file, "w") as f:
                if IS_POSIX:
                    result = subprocess.run(tokens, stdout=f, stderr=subprocess.PIPE, text=True)
                else:
                    result = subprocess.run(["cmd", "/c"] + tokens, stdout=f, stderr=subprocess.PIPE, text=True)
            return result.stderr.decode() if result.stderr else ""
        else:
            if IS_POSIX:
                result = subprocess.run(tokens, capture_output=True, text=True)
            else:
                result = subprocess.run(["cmd", "/c"] + tokens, capture_output=True, text=True)
            output = result.stdout
            if result.stderr:
                output += result.stderr
            return output
    except FileNotFoundError:
        return "Command not found\n"
    except Exception as e:
        return f"{e}\n"

#  GUI Shell 
class ShellGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Python Shell GUI")
        self.geometry("800x500")

        # Terminal widget (editable text area)
        self.terminal = ScrolledText(self, wrap=tk.WORD, bg="black", fg="white", 
                                      font=("Consolas", 12), insertbackground="white")
        self.terminal.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.terminal.bind("<Return>", self.execute_command)
        self.terminal.bind("<KeyPress>", self.on_key_press)
        self.terminal.bind("<Up>", self.navigate_history_up)
        self.terminal.bind("<Down>", self.navigate_history_down)
        self.terminal.focus_set()

        # History navigation
        self.history_index = None
        
        # Track where the prompt starts (to prevent editing previous output)
        self.prompt_position = "1.0"

        # Display initial prompt
        self.show_prompt()

    def on_key_press(self, event):
        """Prevent editing before the prompt."""
        # Allow special keys
        if event.keysym in ("Up", "Down", "Left", "Right", "Home", "End", "BackSpace", "Delete"):
            # Prevent backspace/delete before prompt
            if event.keysym in ("BackSpace", "Delete"):
                cursor_pos = self.terminal.index(tk.INSERT)
                if self.terminal.compare(cursor_pos, "<=", self.prompt_position):
                    return "break"
            # Prevent left arrow/home before prompt
            if event.keysym in ("Left", "BackSpace"):
                cursor_pos = self.terminal.index(tk.INSERT)
                if self.terminal.compare(cursor_pos, "<=", self.prompt_position):
                    return "break"
            return
        
        # Ensure typing happens after the prompt
        cursor_pos = self.terminal.index(tk.INSERT)
        if self.terminal.compare(cursor_pos, "<", self.prompt_position):
            self.terminal.mark_set(tk.INSERT, tk.END)

    def show_prompt(self):
        """Display a new prompt."""
        prompt = self.get_prompt()
        self.terminal.insert(tk.END, prompt)
        self.prompt_position = self.terminal.index(tk.INSERT)
        self.terminal.see(tk.END)

    # File-like write for print redirection
    def write(self, message):
        self.terminal.insert(tk.END, message)
        self.terminal.see(tk.END)

    def flush(self):
        pass

    # Generate PY:\<current_dir> prompt
    def get_prompt(self):
        cwd = os.getcwd()
        parts = cwd.split(os.sep)
        path_part = os.sep.join(parts[1:]) if len(parts) > 1 else ""
        return f"PY:\\{path_part}> "

    # Handle command execution
    def execute_command(self, event=None):
        # Get command from current line
        command = self.terminal.get(self.prompt_position, tk.END).strip()
        
        if not command:
            self.terminal.insert(tk.END, "\n")
            self.show_prompt()
            return "break"

        self.terminal.insert(tk.END, "\n")

        # Exit commands
        if command in ("exit", "quit"):
            self.destroy()
            return "break"

        # History rerun (!n)
        if command.startswith("!"):
            try:
                n = int(command[1:])
                if 1 <= n <= len(history):
                    command = history[n - 1].strip()
                    self.write(f"Re-running command: {command}\n")
                else:
                    self.write("Invalid history reference\n")
                    self.show_prompt()
                    return "break"
            except ValueError:
                self.write("Invalid history reference\n")
                self.show_prompt()
                return "break"

        append_history(command + "\n")
        output = run_command(command)
        if output:
            self.write(output)
        
        self.show_prompt()
        return "break"

    # History navigation with arrows
    def navigate_history_up(self, event=None):
        if not history:
            return "break"
        if self.history_index is None:
            self.history_index = len(history) - 1
        elif self.history_index > 0:
            self.history_index -= 1
        
        # Clear current input and replace with history
        self.terminal.delete(self.prompt_position, tk.END)
        self.terminal.insert(tk.END, history[self.history_index].strip())
        return "break"

    def navigate_history_down(self, event=None):
        if not history or self.history_index is None:
            return "break"
        
        if self.history_index < len(history) - 1:
            self.history_index += 1
            self.terminal.delete(self.prompt_position, tk.END)
            self.terminal.insert(tk.END, history[self.history_index].strip())
        else:
            self.history_index = None
            self.terminal.delete(self.prompt_position, tk.END)
        
        return "break"

#  Run GUI 
if __name__ == "__main__":
    app = ShellGUI()
    app.mainloop()
