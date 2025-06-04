import os
import json

class BoardManager:
    SETS_PATH = os.path.join('config', 'component_sets.json')

    def __init__(self):
        self.sets = {}
        self.load()

    def load(self):
        if os.path.exists(self.SETS_PATH):
            with open(self.SETS_PATH, 'r') as f:
                self.sets = json.load(f)
        else:
            self.sets = {}

    def save(self):
        os.makedirs(os.path.dirname(self.SETS_PATH), exist_ok=True)
        with open(self.SETS_PATH, 'w') as f:
            json.dump(self.sets, f, indent=2)

    def add_set(self, name, components):
        self.sets[name] = components
        self.save()

    def edit_set(self, name, components):
        self.sets[name] = components
        self.save()

    def delete_set(self, name):
        if name in self.sets:
            del self.sets[name]
            self.save()

    def import_sets(self, path):
        with open(path, 'r') as f:
            imported = json.load(f)
        self.sets.update(imported)
        self.save()

    def export_sets(self, path):
        with open(path, 'w') as f:
            json.dump(self.sets, f, indent=2)
