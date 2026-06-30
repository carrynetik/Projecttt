# core/data_structures.py
from dataclasses import dataclass, field
from typing import List

@dataclass
class Item:
    asset_id: str
    class_id: str
    name: str
    type: str          
    rarity: str        
    exterior: str      
    marketable: bool
    tradable: bool
    icon_url: str
    estimated_price: float = 0.0 

@dataclass
class GameStat:
    app_id: int
    name: str
    playtime_forever_hours: float
    icon_url: str

@dataclass
class AccountStatus:
    steam_id: str
    persona_name: str
    avatar_url: str
    avatar_bytes: bytes
    is_vac_banned: bool
    is_community_banned: bool
    economy_ban: str
    days_since_last_ban: int