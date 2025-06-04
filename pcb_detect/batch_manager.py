import os
import json
from datetime import datetime

class BatchManager:
    BATCHES_PATH = os.path.join('results', 'batches.json')

    def __init__(self):
        self.batches = {}
        self.current_batch = 'Default'
        self.load()

    def load(self):
        if os.path.exists(self.BATCHES_PATH):
            with open(self.BATCHES_PATH, 'r') as f:
                self.batches = json.load(f)
        else:
            self.batches = {'Default': []}

    def save(self):
        os.makedirs(os.path.dirname(self.BATCHES_PATH), exist_ok=True)
        with open(self.BATCHES_PATH, 'w') as f:
            json.dump(self.batches, f, indent=2)

    def create_batch(self, name=None):
        if not name:
            name = f"Batch_{datetime.now().strftime('%Y%m%d_%H%M')}"
        self.batches[name] = []
        self.current_batch = name
        self.save()
        return name

    def delete_batch(self, name):
        if name in self.batches and name != 'Default':
            del self.batches[name]
            self.save()

    def add_result(self, result):
        if self.current_batch not in self.batches:
            self.batches[self.current_batch] = []
        self.batches[self.current_batch].append(result)
        self.save()

    def export_batch(self, name, path):
        if name in self.batches:
            with open(path, 'w') as f:
                json.dump(self.batches[name], f, indent=2)
