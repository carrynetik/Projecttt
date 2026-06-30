# core/analytics.py
from typing import List, Dict, Any, Callable
from core.data_structures import Item, GameStat

class InventoryAnalytics:
    @staticmethod
    def merge_sort(items: List[Any], key_extractor: Callable[[Any], Any], reverse: bool = False) -> List[Any]:
        if len(items) <= 1:
            return items
        mid = len(items) // 2
        left_half = InventoryAnalytics.merge_sort(items[:mid], key_extractor, reverse)
        right_half = InventoryAnalytics.merge_sort(items[mid:], key_extractor, reverse)
        return InventoryAnalytics._merge(left_half, right_half, key_extractor, reverse)

    @staticmethod
    def _merge(left, right, key_extractor, reverse):
        result = []
        i = j = 0
        while i < len(left) and j < len(right):
            if not reverse:
                condition = key_extractor(left[i]) <= key_extractor(right[j])
            else:
                condition = key_extractor(left[i]) >= key_extractor(right[j])
            if condition:
                result.append(left[i]); i += 1
            else:
                result.append(right[j]); j += 1
        result.extend(left[i:]); result.extend(right[j:])
        return result

    @staticmethod
    def filter_items(items: List[Any], predicate: Callable[[Any], bool]) -> List[Any]:
        return [item for item in items if predicate(item)]

    @staticmethod
    def calculate_distribution(items: List[Item], attribute_name: str) -> Dict[str, int]:
        distribution = {}
        for item in items:
            val = getattr(item, attribute_name, "Обычное")
            distribution[val] = distribution.get(val, 0) + 1
        return distribution

    @staticmethod
    def get_summary_stats(items: List[Item]) -> Dict[str, Any]:
        total = len(items)
        tradable = sum(1 for item in items if item.tradable)
        marketable = sum(1 for item in items if item.marketable)
        return {"total": total, "tradable": tradable, "marketable": marketable, 
                "tradable_percentage": round((tradable/total*100) if total > 0 else 0, 2)}

    @staticmethod
    def get_library_summary(games: List[GameStat]) -> Dict[str, Any]:
        if not games: return {"total_games": 0, "total_hours": 0, "avg_hours": 0, "top_game": "Нет"}
        total_hours = sum(g.playtime_forever_hours for g in games)
        top_game = max(games, key=lambda x: x.playtime_forever_hours)
        return {"total_games": len(games), "total_hours": round(total_hours, 1), 
                "avg_hours": round(total_hours/len(games), 1), "top_game": top_game.name}

    @staticmethod
    def get_rarity_weight(rarity: str) -> int:
        """Присваивает вес редкости, чтобы Тайное было выше Ширпотреба"""
        r = rarity.lower()
        if "экстраординар" in r or "контрабанд" in r: return 7
        if "тайное" in r: return 6
        if "засекреченное" in r: return 5
        if "запрещенное" in r: return 4
        if "армейское" in r: return 3
        if "промышленное" in r: return 2
        if "ширпотреб" in r: return 1
        return 0