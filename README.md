# PY-Shell
A fully functional command-line shell written in Python — because who doesn't want to build their own terminal from scratch?

A lightweight **Python-based shell** inspired by Unix/Mac terminals, implemented in Python. Supports **command execution, history, pipes, redirection, and directory navigation**. Includes both a **CLI version** and a **GUI version**.  

---

## Features

- Execute system commands (`ls`, `dir`, `mkdir`, etc.)  
- `cd` support with prompt updating (`PY:\<current_dir>`)  
- Command history with `history` command and `!n` rerun support  
- Pipes (`|`) and output redirection (`>`)  
- Cross-platform: Windows and POSIX compatible  
- Two versions:
  - **CLI version:** classic command-line interface  
  - **GUI version:** scrollable terminal with command input
- type exit or quit to close the program


---

## Requirements

- Python 3.8+  
- Works on **Windows, Linux, macOS**  

Optional: For GUI version, no extra packages needed (uses **Tkinter**, included with Python).  

---

## CLI Version

### Run

```bash
python PY.py

PY> mkdir hello
PY> cd hello
PY> echo "Hello World" > file.txt
PY> ls
file.txt
PY> history
[1] mkdir hello
[2] cd hello
[3] echo "Hello World" > file.txt
[4] ls
PY> !3


<img width="1880" height="1295" alt="image" src="https://github.com/user-attachments/assets/a2365cd4-bd3a-4f16-93b4-748b6e2e8587" />
