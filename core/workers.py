# core/workers.py
from PyQt6.QtCore import QThread, pyqtSignal
from core.steam_api import SteamParser

class InventoryFetchWorker(QThread):
    finished = pyqtSignal(list)   
    error = pyqtSignal(str)       
    status_update = pyqtSignal(str) 

    def __init__(self, steam_id: str):
        super().__init__()
        self.steam_id = steam_id
        self.parser = SteamParser()

    def run(self):
        self.status_update.emit("Скачивание полного инвентаря...")
        try:
            inventory = self.parser.fetch_inventory(self.steam_id)
            if not inventory:
                self.error.emit("Не удалось получить инвентарь. Возможно, профиль скрыт.")
            else:
                self.status_update.emit(f"Успешно загружено предметов: {len(inventory)}")
                self.finished.emit(inventory)
        except Exception as e:
            self.error.emit(f"Критическая ошибка: {str(e)}")


class LibraryFetchWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    status_update = pyqtSignal(str)

    def __init__(self, steam_id: str):
        super().__init__()
        self.steam_id = steam_id
        self.parser = SteamParser()

    def run(self):
        self.status_update.emit("Загрузка библиотеки игр...")
        try:
            games = self.parser.fetch_library(self.steam_id)
            if not games:
                self.error.emit("Не удалось прочитать игры. Профиль скрыт.")
            else:
                self.status_update.emit(f"Успешно обработано игр: {len(games)}")
                self.finished.emit(games)
        except Exception as e:
            self.error.emit(f"Критическая ошибка: {str(e)}")


class AccountFetchWorker(QThread):
    finished = pyqtSignal(object) 
    error = pyqtSignal(str)

    def __init__(self, steam_id: str):
        super().__init__()
        self.steam_id = steam_id
        self.parser = SteamParser()

    def run(self):
        try:
            status = self.parser.fetch_account_status(self.steam_id)
            if status:
                self.finished.emit(status)
            else:
                self.error.emit("Не удалось получить статус аккаунта.")
        except Exception as e:
            self.error.emit(f"Ошибка проверки аккаунта: {str(e)}")