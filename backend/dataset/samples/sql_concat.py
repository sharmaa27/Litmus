def lookup(cur, email):
    cur.execute("SELECT * FROM u WHERE email = '" + email + "'")  # EXPECT: PY-SQL-001
