def get_user(cur, uid):
    cur.execute(f"SELECT * FROM users WHERE id = {uid}")  # EXPECT: PY-SQL-001
    return cur.fetchone()
