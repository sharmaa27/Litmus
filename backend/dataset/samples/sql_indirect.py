def lookup(cur, name):
    query = "SELECT * FROM u WHERE name = '" + name + "'"
    cur.execute(query)  # EXPECT: PY-SQL-001
