import hashlib

def digest(s):
    return hashlib.sha256(s.encode()).hexdigest()
