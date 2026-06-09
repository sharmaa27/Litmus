def get_user(cur, uid):
    cur.execute("SELECT * FROM users WHERE id = ?", (uid,))
    return cur.fetchone()
