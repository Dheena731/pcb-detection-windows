# Handles model upload/load/delete logic
import os
import shutil

class ModelManager:
    MODELS_DIR = 'models'

    @staticmethod
    def list_models():
        if not os.path.exists(ModelManager.MODELS_DIR):
            os.makedirs(ModelManager.MODELS_DIR)
        return [f for f in os.listdir(ModelManager.MODELS_DIR) if f.endswith('.pt')]

    @staticmethod
    def upload_model(src_path):
        os.makedirs(ModelManager.MODELS_DIR, exist_ok=True)
        dst = os.path.join(ModelManager.MODELS_DIR, os.path.basename(src_path))
        shutil.copy2(src_path, dst)
        return dst

    @staticmethod
    def delete_model(model_name):
        path = os.path.join(ModelManager.MODELS_DIR, model_name)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
