import yaml

def parse(text):
    return yaml.load(text, Loader=yaml.SafeLoader)

def parse2(text):
    return yaml.safe_load(text)
