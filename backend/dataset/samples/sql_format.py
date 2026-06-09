def q(cur, role):
    cur.execute("SELECT * FROM u WHERE role = {}".format(role))  # EXPECT: PY-SQL-001
