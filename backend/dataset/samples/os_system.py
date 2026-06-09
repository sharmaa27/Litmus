import os

def cleanup(path):
    os.system("rm -rf " + path)  # EXPECT: PY-SHELL-001
