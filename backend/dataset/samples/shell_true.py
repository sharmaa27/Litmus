import subprocess

def ping(host):
    subprocess.run("ping " + host, shell=True)  # EXPECT: PY-SHELL-001
