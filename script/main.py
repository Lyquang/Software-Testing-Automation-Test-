import sys
import subprocess
import os

files = [f for f in os.listdir() if f.endswith(".py") and f != "main.py"]

if len(sys.argv) < 2:
    print("Sử dụng: python main.py <filename.py> | all")
    exit()

arg = sys.argv[1]

if arg == "all":
    for file in files:
        subprocess.run(["python", file])
elif arg in files:
    subprocess.run(["python", arg])
else:
    print("File không tồn tại!")
