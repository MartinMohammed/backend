from pathlib import Path
import json
import shutil
from typing import Dict, Any
from app.core.logging import LoggerMixin

class FileManager(LoggerMixin):
    BASE_DATA_DIR = Path("data")
    DEFAULT_DIR = BASE_DATA_DIR / "default"
    
    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure all required directories exist"""
        cls.BASE_DATA_DIR.mkdir(exist_ok=True)
        cls.DEFAULT_DIR.mkdir(exist_ok=True)

    @classmethod
    def create_session_directory(cls, session_id: str) -> Path:
        """Create a new directory for the session"""
        session_dir = cls.BASE_DATA_DIR / session_id
        session_dir.mkdir(exist_ok=True)
        return session_dir

    @classmethod
    def save_session_data(cls, session_id: str, names: Dict, player_details: Dict, wagons: Dict) -> None:
        """Save the three main data files for a session"""
        session_dir = cls.create_session_directory(session_id)
        
        # Save each file
        files_to_save = {
            "names.json": names,
            "player_details.json": player_details,
            "wagons.json": wagons
        }
        
        for filename, data in files_to_save.items():
            file_path = session_dir / filename
            cls.save_json(file_path, data)
            cls.get_logger().info(f"Saved {filename} for session {session_id}")

    @classmethod
    def get_data_directory(cls, session_id: str, default_game: bool) -> Path:
        """Get the appropriate data directory based on default_game flag"""
        if default_game:
            return cls.DEFAULT_DIR
        return cls.BASE_DATA_DIR / session_id

    @classmethod
    def load_session_data(cls, session_id: str, default_game: bool = True) -> tuple[Dict, Dict, Dict]:
        """Load all data files for a session"""
        data_dir = cls.get_data_directory(session_id, default_game)
        if not data_dir.exists():
            cls.get_logger().error(f"Data directory not found: {data_dir}")
            raise FileNotFoundError(f"No data found for session {session_id}")

        try:
            names = cls.load_json(data_dir / "names.json")
            player_details = cls.load_json(data_dir / "player_details.json")
            wagons = cls.load_json(data_dir / "wagons.json")
            
            cls.get_logger().info(
                f"Loaded session data from {'default' if default_game else 'session'} directory",
                extra={
                    "session_id": session_id,
                    "directory": str(data_dir)
                }
            )
            return names, player_details, wagons
            
        except FileNotFoundError as e:
            cls.get_logger().error(f"Failed to load required files from {data_dir}: {str(e)}")
            raise FileNotFoundError(f"Missing required data files in {data_dir}")

    @staticmethod
    def save_json(file_path: Path, data: Dict[str, Any]) -> None:
        """Save data to a JSON file"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def load_json(file_path: Path) -> Dict:
        """Load data from a JSON file"""
        with open(file_path, 'r') as f:
            return json.load(f) 