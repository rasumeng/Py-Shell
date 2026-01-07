import os
import shlex
import subprocess
import signal
import sys

IS_POSIX = os.name == "posix"
MAX_HISTORY = 50
history = []

# Ignore Ctrl+C in the shell
signal.signal(signal.SIGINT, signal.SIG_IGN)
if hasattr(signal, "SIGTSTP"):
    signal.signal(signal.SIGTSTP, signal.SIG_IGN)


def windows_wrap(tokens):
    """Wrap command for Windows built-in execution"""
    return ["cmd", "/c"] + tokens


def get_prompt():
    """Return the prompt in PY:\\<current_dir> style"""
    cwd = os.getcwd()
    # Split path into parts and skip the drive letter for Windows
    parts = cwd.split(os.sep)
    if len(parts) > 1:
        path_part = os.sep.join(parts[1:])
    else:
        path_part = ""
    return f"PY:\\{path_part}> "


def append_history(command):
    if not command.strip():
        return
    history.append(command)
    if len(history) > MAX_HISTORY:
        history.pop(0)


def display_history():
    for i, cmd in enumerate(history, start=1):
        print(f"[{i}] {cmd}", end="")


def rerun_command(command):
    print(f"Re-running command: {command}", end="")
    run_command(command)


def run_command(command_string):
    try:
        tokens = shlex.split(command_string)
    except ValueError:
        return

    if not tokens:
        return

    redirect_file = None

    # -------- Built-ins --------
    if tokens[0] == "cd":
        if len(tokens) < 2:
            print("cd: expected argument")
        else:
            try:
                os.chdir(tokens[1])
            except OSError as e:
                print(f"cd failed: {e}")
        return

    if tokens[0] == "history":
        display_history()
        return

    # -------- Output Redirection --------
    if ">" in tokens:
        idx = tokens.index(">")
        if idx + 1 >= len(tokens):
            print("No file specified for redirection")
            return
        redirect_file = tokens[idx + 1]
        tokens = tokens[:idx]

    # -------- Pipe Handling --------
    if "|" in tokens:
        pipe_index = tokens.index("|")
        left_cmd = tokens[:pipe_index]
        right_cmd = tokens[pipe_index + 1:]

        try:
            if IS_POSIX:
                p1 = subprocess.Popen(left_cmd, stdout=subprocess.PIPE, preexec_fn=os.setsid)
                p2 = subprocess.Popen(right_cmd, stdin=p1.stdout, preexec_fn=os.setsid)
            else:
                p1 = subprocess.Popen(windows_wrap(left_cmd), stdout=subprocess.PIPE)
                p2 = subprocess.Popen(windows_wrap(right_cmd), stdin=p1.stdout)

            p1.stdout.close()
            p2.wait()

        except FileNotFoundError:
            print("Command not found")
        return

    # -------- Normal Execution --------
    try:
        if redirect_file:
            with open(redirect_file, "w") as f:
                if IS_POSIX:
                    subprocess.run(tokens, stdout=f, preexec_fn=os.setsid)
                else:
                    subprocess.run(windows_wrap(tokens), stdout=f)
        else:
            if IS_POSIX:
                subprocess.run(tokens, preexec_fn=os.setsid)
            else:
                subprocess.run(windows_wrap(tokens))

    except FileNotFoundError:
        print("Command not found")


def main():
    while True:
        try:
            command = input(get_prompt())
        except EOFError:
            break

        if not command.strip():
            continue

        if command in ("exit", "quit"):
            sys.exit(0)

        # History rerun
        if command.startswith("!"):
            try:
                n = int(command[1:])
                if 1 <= n <= len(history):
                    rerun_command(history[n - 1])
                else:
                    print("Invalid history reference")
            except ValueError:
                print("Invalid history reference")
            continue

        append_history(command + "\n")
        run_command(command)


if __name__ == "__main__":
    main()
