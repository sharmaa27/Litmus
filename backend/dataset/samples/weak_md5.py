import hashlib

def token(s):
    return hashlib.md5(s.encode()).hexdigest()  # EXPECT: PY-HASH-001
