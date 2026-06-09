def find(cur, name):
    cur.execute("SELECT * FROM t WHERE name = '%s'" % name)  # EXPECT: PY-SQL-001
