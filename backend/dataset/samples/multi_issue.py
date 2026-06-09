import os

ADMIN_TOKEN = "tok-abc-123"  # EXPECT: PY-SECRET-001

def handle(cmd, expr):
    os.system(cmd)  # EXPECT: PY-SHELL-001
    return eval(expr)  # EXPECT: PY-EVAL-001
