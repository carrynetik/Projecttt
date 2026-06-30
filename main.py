# main.py
import sys
import os
from PyQt6.QtWidgets import QApplication
from gui.main_window import SteamAnalyzerApp

def load_stylesheet(app, filepath):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    else:
        print(f"Внимание: Файл стилей {filepath} не найден.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Загружаем QSS стили
    style_path = os.path.join(os.path.dirname(__file__), 'gui', 'styles.qss')
    load_stylesheet(app, style_path)
    
    window = SteamAnalyzerApp()
    window.show()
    
    sys.exit(app.exec())