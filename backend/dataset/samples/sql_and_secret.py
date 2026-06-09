SESSION_SECRET = "abc123-session"  # EXPECT: PY-SECRET-001

def rows(cur, kind):
    cur.execute(f"SELECT * FROM logs WHERE kind = {kind}")  # EXPECT: PY-SQL-001
