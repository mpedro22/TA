import os
from dataclasses import dataclass

@dataclass
class Config:
    # Data URLs
    TRANSPORT_DATA_URL: str = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid=155140281"
    ELECTRONIC_DATA_URL: str = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid=622151341"
    ACTIVITIES_DATA_URL: str = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid=1749257811"
    RESPONDEN_DATA_URL: str = "https://docs.google.com/spreadsheets/d/11Y7cx9SqtLeG5S09F34nDQSnwaZDfUkZKVnNwRLi8V4/export?format=csv&gid=1606042726"
    
    # App settings
    CACHE_TTL: int = 3600
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Paths
    DATA_PATH: str = "data"
    USERS_FILE: str = "data/users.json"

config = Config()
