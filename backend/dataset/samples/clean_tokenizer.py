def tokenize(line):
    default_token = "<PAD>"
    parts = line.split(",")
    return parts or [default_token]
