# core/steam_api.py
import requests
import time
from typing import Optional, Dict, List
from core.data_structures import Item, GameStat, AccountStatus

class SteamParser:
    def __init__(self):
        self.api_key = "A64C319FB7E91FC6435FD14A06F81FA5" 
        
        self.base_inventory_url = "https://steamcommunity.com/inventory/{steam_id}/730/2"
        self.base_games_api_url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
        self.base_bans_url = "http://api.steampowered.com/ISteamUser/GetPlayerBans/v1/"
        self.base_summaries_url = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_inventory(self, steam_id: str) -> List[Item]:
        items_list = []
        last_assetid = None
        more_items = True
        
        while more_items:
            params = {'l': 'russian', 'count': 1000}
            if last_assetid:
                params['start_assetid'] = last_assetid

            try:
                response = self.session.get(self.base_inventory_url.format(steam_id=steam_id), params=params, timeout=10)
                if response.status_code == 429:
                    time.sleep(15)
                    continue
                if response.status_code != 200:
                    break

                data = response.json()
                parsed_items = self._parse_items_from_json(data)
                items_list.extend(parsed_items)

                more_items = data.get('more_items', 0) == 1
                last_assetid = data.get('last_assetid')
                time.sleep(1) 
            except Exception:
                break
        return items_list

    def _parse_items_from_json(self, data: Dict) -> List[Item]:
        if not data or 'assets' not in data or 'descriptions' not in data:
            return []

        descriptions_map = {
            f"{desc['classid']}_{desc.get('instanceid', '0')}": desc 
            for desc in data['descriptions']
        }

        parsed_items = []
        for asset in data['assets']:
            key = f"{asset['classid']}_{asset.get('instanceid', '0')}"
            desc = descriptions_map.get(key)
            
            if desc:
                rarity = self._extract_tag(desc, 'Rarity', 'Обычное')
                exterior = self._extract_tag(desc, 'Exterior', 'Неприменимо')
                
                raw_type = desc.get('type', 'Разное')
                clean_type = raw_type.replace(rarity, '').strip().capitalize()
                
                item = Item(
                    asset_id=asset['assetid'],
                    class_id=asset['classid'],
                    name=desc.get('market_name', 'Неизвестно'),
                    type=clean_type if clean_type else raw_type,
                    rarity=rarity,
                    exterior=exterior,
                    marketable=bool(desc.get('marketable')),
                    tradable=bool(desc.get('tradable')),
                    icon_url=f"https://community.akamai.steamstatic.com/economy/image/{desc.get('icon_url')}"
                )
                parsed_items.append(item)
        return parsed_items
        
    def _extract_tag(self, desc: Dict, category: str, default: str) -> str:
        for tag in desc.get('tags', []):
            if tag.get('category') == category:
                return tag.get('localized_tag_name', default)
        return default

    def fetch_library(self, steam_id: str) -> List[GameStat]:
        if not self.api_key: return []
        try:
            params = {'key': self.api_key, 'steamid': steam_id, 'format': 'json', 'include_appinfo': '1', 'include_played_free_games': '1'}
            response = self.session.get(self.base_games_api_url, params=params, timeout=10)
            if response.status_code != 200: return []
            data = response.json()
            if 'response' not in data or 'games' not in data['response']: return []
                
            parsed_games = []
            for g in data['response']['games']:
                playtime_hours = round(g.get('playtime_forever', 0) / 60.0, 1)
                game_stat = GameStat(app_id=int(g.get('appid', 0)), name=g.get('name', 'Неизвестная игра'), playtime_forever_hours=playtime_hours, icon_url="")
                parsed_games.append(game_stat)
            return parsed_games
        except Exception:
            return []

    def fetch_account_status(self, steam_id: str) -> Optional[AccountStatus]:
        if not self.api_key: return None
        try:
            bans_resp = self.session.get(self.base_bans_url, params={'key': self.api_key, 'steamids': steam_id}, timeout=10).json()
            sums_resp = self.session.get(self.base_summaries_url, params={'key': self.api_key, 'steamids': steam_id}, timeout=10).json()
            
            ban_data = bans_resp.get('players', [{}])[0]
            sum_data = sums_resp.get('response', {}).get('players', [{}])[0]
            
            if not ban_data or not sum_data: return None
            
            avatar_url = sum_data.get('avatarfull', '')
            avatar_bytes = b""
            if avatar_url:
                try:
                    avatar_bytes = self.session.get(avatar_url, timeout=5).content
                except Exception:
                    avatar_bytes = b""

            return AccountStatus(
                steam_id=steam_id,
                persona_name=sum_data.get('personaname', 'Неизвестно'),
                avatar_url=avatar_url,
                avatar_bytes=avatar_bytes,
                is_vac_banned=ban_data.get('VACBanned', False),
                is_community_banned=ban_data.get('CommunityBanned', False),
                economy_ban=ban_data.get('EconomyBan', 'none'),
                days_since_last_ban=ban_data.get('DaysSinceLastBan', 0)
            )
        except Exception:
            return None