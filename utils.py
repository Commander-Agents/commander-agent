import json

CONFIG_PATH = "config.json"

def load_config():
    """Charge la configuration depuis le fichier JSON."""
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)