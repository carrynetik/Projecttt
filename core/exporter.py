# core/exporter.py
import os
from typing import List
from datetime import datetime
from core.data_structures import Item, GameStat
from core.analytics import InventoryAnalytics

class ReportGenerator:
    
    # Цвета редкостей CS2
    RARITY_COLORS = {
        "экстраординар": "#e4ae39", "контрабанд": "#e4ae39",
        "тайн": "#eb4b4b", "засекреч": "#d32ce6", 
        "запрещ": "#8847ff", "армейск": "#4b69ff", 
        "промышлен": "#5e98d9", "ширпотреб": "#b0c3d9"
    }

    @classmethod
    def get_color_for_rarity(cls, rarity: str) -> str:
        r_lower = rarity.lower()
        for key, color in cls.RARITY_COLORS.items():
            if key in r_lower:
                return color
        return "#ffffff"

    @staticmethod
    def build_summary_text(steam_id: str, inventory: List[Item], games: List[GameStat], as_html: bool = False) -> str:
        report = []
        
        if as_html:
            report.append(f"<h2 style='color: #3b82f6; margin-bottom: 5px;'>АНАЛИТИЧЕСКИЙ ОТЧЕТ ПРОФИЛЯ</h2>")
            report.append(f"<b>SteamID64:</b> {steam_id if steam_id else 'Не указан'}<br>")
            report.append(f"<b>Дата генерации:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br><hr>")
            report.append("<h3 style='color: #10b981;'>[1] СВОДКА ПО ИНВЕНТАРЮ CS2:</h3>")
        else:
            report.append("="*50)
            report.append(f" АНАЛИТИЧЕСКИЙ ОТЧЕТ ПРОФИЛЯ STEAM ")
            report.append("="*50)
            report.append(f"SteamID64: {steam_id if steam_id else 'Не указан'}")
            report.append(f"Дата генерации: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append("-" * 50)
            report.append("\n[1] СВОДКА ПО ИНВЕНТАРЮ CS2:")

        if not inventory:
            report.append("Данные об инвентаре не загружены или инвентарь пуст." + ("<br>" if as_html else ""))
        else:
            stats = InventoryAnalytics.get_summary_stats(inventory)
            nl = "<br>" if as_html else "\n"
            report.append(f"Всего предметов: <b>{stats['total']}</b>{nl}" if as_html else f"Всего предметов: {stats['total']}")
            report.append(f"Из них можно продать (Marketable): <b>{stats['marketable']}</b>{nl}" if as_html else f"Из них можно продать (Marketable): {stats['marketable']}")
            report.append(f"Из них можно обменять (Tradable): <b>{stats['tradable']}</b> ({stats['tradable_percentage']}%){nl}" if as_html else f"Из них можно обменять (Tradable): {stats['tradable']} ({stats['tradable_percentage']}%)")
            
            report.append(f"{nl}<b>Распределение по редкости:</b>{nl}" if as_html else "\nРаспределение по редкости:")
            dist = InventoryAnalytics.calculate_distribution(inventory, "rarity")
            
            # Сортируем редкости по значимости (от Тайного к Ширпотребу)
            sorted_rarities = sorted(dist.items(), key=lambda x: InventoryAnalytics.get_rarity_weight(x[0]), reverse=True)
            
            for rarity, count in sorted_rarities:
                if as_html:
                    color = ReportGenerator.get_color_for_rarity(rarity)
                    report.append(f" - <span style='color: {color}; font-weight: bold;'>{rarity}</span>: {count} шт.<br>")
                else:
                    report.append(f" - {rarity}: {count} шт.")
                
        if as_html:
            report.append("<h3 style='color: #10b981;'>[2] СВОДКА ПО БИБЛИОТЕКЕ ИГР:</h3>")
        else:
            report.append("\n[2] СВОДКА ПО БИБЛИОТЕКЕ ИГР:")

        if not games:
            report.append("Данные о библиотеке игр не загружены или профиль скрыт." + ("<br>" if as_html else ""))
        else:
            lib_summary = InventoryAnalytics.get_library_summary(games)
            nl = "<br>" if as_html else "\n"
            report.append(f"Всего игр на аккаунте: <b>{lib_summary['total_games']}</b>{nl}" if as_html else f"Всего игр на аккаунте: {lib_summary['total_games']}")
            report.append(f"Общее время во всех играх: <b>{lib_summary['total_hours']} ч.</b>{nl}" if as_html else f"Общее время во всех играх: {lib_summary['total_hours']} ч.")
            report.append(f"Среднее время на одну игру: <b>{lib_summary['avg_hours']} ч.</b>{nl}" if as_html else f"Среднее время на одну игру: {lib_summary['avg_hours']} ч.")
            
            report.append(f"{nl}<b>ТОП-5 игр по количеству часов:</b>{nl}" if as_html else "\nТОП-5 игр по количеству часов:")
            sorted_games = InventoryAnalytics.merge_sort(games, key_extractor=lambda x: x.playtime_forever_hours, reverse=True)
            for i, game in enumerate(sorted_games[:5], 1):
                report.append(f" {i}. {game.name} — {game.playtime_forever_hours} ч." + ("<br>" if as_html else ""))
                
        if as_html:
            report.append("<hr><i style='color: #888888;'>Отчет сгенерирован в приложении Steam Profile Analyzer.</i>")
        else:
            report.append("\n" + "="*50)
            report.append("Отчет сгенерирован в приложении Steam Profile Analyzer.")
            report.append("="*50)
            
        return "".join(report) if as_html else "\n".join(report)

    @staticmethod
    def export_to_txt(filepath: str, content: str) -> bool:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False