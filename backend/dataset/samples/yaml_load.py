import yaml

def parse(text):
    return yaml.load(text)  # EXPECT: PY-YAML-001
