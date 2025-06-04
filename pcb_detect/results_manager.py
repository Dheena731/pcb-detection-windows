# Handles Excel and snapshot export logic
import os
import pandas as pd
from datetime import datetime
from PIL import Image

class ResultsManager:
    RESULTS_PATH = os.path.join('results', 'detection_results.xlsx')
    BACKUP_DIR = os.path.join('results', 'backups')
    SNAPSHOT_DIR = 'snapshots'

    def __init__(self):
        os.makedirs(self.BACKUP_DIR, exist_ok=True)
        os.makedirs(self.SNAPSHOT_DIR, exist_ok=True)

    def save_result(self, result):
        df = pd.DataFrame([result])
        if os.path.exists(self.RESULTS_PATH):
            df_existing = pd.read_excel(self.RESULTS_PATH)
            df = pd.concat([df_existing, df], ignore_index=True)
        df.to_excel(self.RESULTS_PATH, index=False)
        # Backup
        backup_path = os.path.join(self.BACKUP_DIR, f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        df.to_excel(backup_path, index=False)

    def save_snapshot(self, image, name=None):
        if not name:
            name = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        path = os.path.join(self.SNAPSHOT_DIR, name)
        if isinstance(image, Image.Image):
            image.save(path)
        else:
            Image.fromarray(image).save(path)
        return path
