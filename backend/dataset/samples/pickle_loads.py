import pickle

def load(blob):
    return pickle.loads(blob)  # EXPECT: PY-PICKLE-001
