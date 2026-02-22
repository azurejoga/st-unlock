"""
Data models for SteamUnlocked API
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class Game:
    """Basic game information from search results"""
    title: str
    url: str
    thumbnail: Optional[str] = None
    release_date: Optional[str] = None


@dataclass
class SystemRequirements:
    """System requirements for a game"""
    os: Optional[str] = None
    processor: Optional[str] = None
    memory: Optional[str] = None
    graphics: Optional[str] = None
    storage: Optional[str] = None


@dataclass
class GameDetails(Game):
    """Detailed game information"""
    description: str = ""
    screenshots: List[str] = field(default_factory=list)
    system_requirements: Optional[SystemRequirements] = None
    download_page_url: Optional[str] = None
    file_size: Optional[str] = None
    genre: List[str] = field(default_factory=list)
    developer: Optional[str] = None
    publisher: Optional[str] = None
    release_date_full: Optional[str] = None


@dataclass
class DownloadInfo:
    """Download information for a game"""
    file_host: str  # e.g., "UploadHaven", "MegaUp", etc.
    download_url: str
    file_size: Optional[str] = None
    direct_link: Optional[str] = None  # After bypass
    wait_time: Optional[int] = None  # Seconds to wait


@dataclass
class CategoryInfo:
    """Category information"""
    name: str
    slug: str
    url: str
    game_count: Optional[int] = None


# Available categories on SteamUnlocked
CATEGORIES = [
    "ACTION",
    "ADULT",
    "ADVENTURE",
    "ANIME",
    "CLASSICS",
    "FPS",
    "HORROR",
    "INDIE",
    "OPEN WORLD",
    "POPULAR",
    "PS2",
    "RACING",
    "REMASTERED",
    "RPG",
    "SIMULATION",
    "SMALL GAMES",
    "SPORTS",
    "VIRTUAL REALITY"
]
