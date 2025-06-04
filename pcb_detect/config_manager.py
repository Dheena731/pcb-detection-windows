import json
import os

class ConfigManager:
    CONFIG_PATH = os.path.join('config', 'config.json')
    DEFAULTS = {
        'confidence': 0.5,
        'delay': 0.5,
        'last_model': '',
        'last_board': '',
        'auto_save_snapshots': True,
        'batch_processing': False
    }

    def __init__(self):
        self.config = self.DEFAULTS.copy()
        self.load()

    def load(self):
        if os.path.exists(self.CONFIG_PATH):
            try:
                with open(self.CONFIG_PATH, 'r') as f:
                    self.config.update(json.load(f))
            except Exception:
                pass

    def save(self):
        os.makedirs(os.path.dirname(self.CONFIG_PATH), exist_ok=True)
        with open(self.CONFIG_PATH, 'w') as f:
            json.dump(self.config, f, indent=2)

    def get(self, key):
        return self.config.get(key, self.DEFAULTS.get(key))

    def set(self, key, value):
        self.config[key] = value
        self.save()
