import os
from dataclasses import dataclass

@dataclass
class AppConfig:
    """Application configuration dataclass."""
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'edusync-super-secret-key-2024')
    DATABASE_PATH: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database', 'edusync.db')
    QR_EXPIRY_SECONDS: int = 30
    UPLOAD_FOLDER: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH: int = 10 * 1024 * 1024  # 10MB max upload

    @classmethod
    def get_config(cls) -> 'AppConfig':
        return cls()
