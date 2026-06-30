# gui/main_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QListWidget, QStackedWidget, QLabel, QPushButton, 
                             QLineEdit, QTableWidget, QTableWidgetItem, QComboBox, 
                             QHeaderView, QMessageBox, QStatusBar, QTabWidget, 
                             QGridLayout, QPlainTextEdit, QFileDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage

from core.workers import InventoryFetchWorker, LibraryFetchWorker, AccountFetchWorker
from core.analytics import InventoryAnalytics
from core.exporter import ReportGenerator
from core.data_structures import Item, GameStat
from gui.charts import InventoryChartWidget, LibraryChartWidget


class SteamAnalyzerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steam Profile & Inventory Analyzer v4.0 (Pro)")
        self.resize(1300, 800)
        
        self.current_inventory = []
        self.current_games = []
        self.last_used_steam_id = ""
        
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(240)
        self.sidebar.addItem("Анализ инвентаря CS2")
        self.sidebar.addItem("Статистика библиотеки игр")
        self.sidebar.addItem("Сводка и Анализ Аккаунта")
        self.sidebar.currentRowChanged.connect(self.display_page)

        self.pages = QStackedWidget()
        self.pages.addWidget(self.create_inventory_page())
        self.pages.addWidget(self.create_library_page())
        self.pages.addWidget(self.create_summary_page())

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.pages)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Приложение готово к работе.")

        self.sidebar.setCurrentRow(0)

    def create_inventory_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(15, 15, 15, 15)
        
        search_layout = QHBoxLayout()
        self.inv_steam_id_input = QLineEdit()
        self.inv_steam_id_input.setPlaceholderText("Введите SteamID64 профиля для анализа инвентаря...")
        self.inv_analyze_btn = QPushButton("Анализировать полный инвентарь")
        self.inv_analyze_btn.clicked.connect(self.start_inventory_loading)
        
        search_layout.addWidget(self.inv_steam_id_input)
        search_layout.addWidget(self.inv_analyze_btn)
        layout.addLayout(search_layout)

        self.tabs = QTabWidget()
        
        table_tab = QWidget()
        table_layout = QVBoxLayout(table_tab)
        
        filter_layout = QHBoxLayout()
        self.inv_sort_box = QComboBox()
        self.inv_sort_box.addItems(["Без сортировки", "По названию (А-Я)", "По названию (Я-А)", "По редкости"])
        self.inv_sort_box.currentIndexChanged.connect(self.apply_inventory_sorting)
        
        self.inv_filter_box = QComboBox()
        self.inv_filter_box.addItems(["Все предметы", "Только торгуемые (Tradable)", "Только продаваемые (Marketable)"])
        self.inv_filter_box.currentIndexChanged.connect(self.apply_inventory_sorting)
        
        filter_layout.addWidget(QLabel("Сортировка (MergeSort):"))
        filter_layout.addWidget(self.inv_sort_box)
        filter_layout.addWidget(QLabel("Фильтрация:"))
        filter_layout.addWidget(self.inv_filter_box)
        filter_layout.addStretch()
        
        self.inv_table = QTableWidget()
        self.inv_table.setColumnCount(5) 
        self.inv_table.setHorizontalHeaderLabels(["Название предмета", "Тип", "Редкость", "Качество", "Asset ID"])
        self.inv_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.inv_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.inv_table.setColumnWidth(0, 300)
        self.inv_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        table_layout.addLayout(filter_layout)
        table_layout.addWidget(self.inv_table)
        
        dashboard_tab = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_tab)
        self.inv_chart_widget = InventoryChartWidget(self)
        dashboard_layout.addWidget(self.inv_chart_widget)
        
        self.tabs.addTab(table_tab, "Детальная таблица (PRO)")
        self.tabs.addTab(dashboard_tab, "Визуальная аналитика")
        
        layout.addWidget(self.tabs)
        return page

    def create_library_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(15, 15, 15, 15)

        search_layout = QHBoxLayout()
        self.lib_steam_id_input = QLineEdit()
        self.lib_steam_id_input.setPlaceholderText("Введите SteamID64 профиля для анализа библиотеки игр...")
        self.lib_analyze_btn = QPushButton("Загрузить библиотеку игр")
        self.lib_analyze_btn.clicked.connect(self.start_library_loading)
        
        search_layout.addWidget(self.lib_steam_id_input)
        search_layout.addWidget(self.lib_analyze_btn)
        layout.addLayout(search_layout)

        self.stats_grid = QGridLayout()
        self.lbl_total_games = QLabel("Всего игр: —")
        self.lbl_total_hours = QLabel("Общее время: —")
        self.lbl_top_game = QLabel("Главная игра: —")
        
        self.stats_grid.addWidget(self.lbl_total_games, 0, 0)
        self.stats_grid.addWidget(self.lbl_total_hours, 0, 1)
        self.stats_grid.addWidget(self.lbl_top_game, 0, 2)
        layout.addLayout(self.stats_grid)

        self.lib_tabs = QTabWidget()
        
        lib_table_tab = QWidget()
        lib_table_layout = QVBoxLayout(lib_table_tab)
        
        lib_filter_layout = QHBoxLayout()
        self.lib_sort_box = QComboBox()
        self.lib_sort_box.addItems(["Без сортировки", "По времени в игре (Убывание)", "По времени в игре (Возрастание)", "По названию (А-Я)"])
        self.lib_sort_box.currentIndexChanged.connect(self.apply_library_sorting)
        lib_filter_layout.addWidget(QLabel("Сортировка игр (MergeSort):"))
        lib_filter_layout.addWidget(self.lib_sort_box)
        lib_filter_layout.addStretch()
        
        self.lib_table = QTableWidget()
        self.lib_table.setColumnCount(3)
        self.lib_table.setHorizontalHeaderLabels(["App ID", "Название игры", "Время в игре (Часы)"])
        self.lib_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.lib_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        lib_table_layout.addLayout(lib_filter_layout)
        lib_table_layout.addWidget(self.lib_table)

        lib_chart_tab = QWidget()
        lib_chart_layout = QVBoxLayout(lib_chart_tab)
        self.lib_chart_widget = LibraryChartWidget(self)
        lib_chart_layout.addWidget(self.lib_chart_widget)

        self.lib_tabs.addTab(lib_table_tab, "Список игр профиля")
        self.lib_tabs.addTab(lib_chart_tab, "Диаграмма ТОП-игр")
        layout.addWidget(self.lib_tabs)

        return page

    def create_summary_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Анализ безопасности аккаунта и Сводный отчет")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #3b82f6;")
        layout.addWidget(title)

        # Интерактивная карточка со статусом банов, ссылкой и аватаркой
        self.account_panel = QWidget()
        self.account_panel.setStyleSheet("background-color: #2b2b36; border-radius: 8px; padding: 15px;")
        account_layout = QHBoxLayout(self.account_panel)
        
        self.lbl_avatar = QLabel()
        self.lbl_avatar.setFixedSize(64, 64)
        self.lbl_avatar.setStyleSheet("background-color: #1e1e24; border-radius: 6px; border: none;")
        self.lbl_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        info_layout = QGridLayout()
        self.lbl_acc_name = QLabel("Никнейм: —")
        self.lbl_acc_name.setOpenExternalLinks(True)
        self.lbl_acc_vac = QLabel("VAC Бан: —")
        self.lbl_acc_comm = QLabel("Бан сообщества: —")
        self.lbl_acc_econ = QLabel("Трейд Бан: —")
        
        info_layout.addWidget(self.lbl_acc_name, 0, 0)
        info_layout.addWidget(self.lbl_acc_vac, 0, 1)
        info_layout.addWidget(self.lbl_acc_comm, 1, 0)
        info_layout.addWidget(self.lbl_acc_econ, 1, 1)
        
        account_layout.addWidget(self.lbl_avatar)
        account_layout.addLayout(info_layout)
        account_layout.addStretch()
        
        layout.addWidget(self.account_panel)

        control_layout = QHBoxLayout()
        self.check_acc_btn = QPushButton("Проверить VAC и статус аккаунта")
        self.check_acc_btn.setMinimumHeight(40)
        self.check_acc_btn.setStyleSheet("background-color: #8b5cf6;")
        self.check_acc_btn.clicked.connect(self.check_account_status)
        
        self.generate_report_btn = QPushButton("Сгенерировать сводный отчет")
        self.generate_report_btn.setMinimumHeight(40)
        self.generate_report_btn.clicked.connect(self.generate_report)
        
        self.export_report_btn = QPushButton("Экспортировать в TXT")
        self.export_report_btn.setMinimumHeight(40)
        self.export_report_btn.setEnabled(False) 
        self.export_report_btn.setStyleSheet("background-color: #10b981; color: white;") 
        self.export_report_btn.clicked.connect(self.export_report)

        control_layout.addWidget(self.check_acc_btn)
        control_layout.addWidget(self.generate_report_btn)
        control_layout.addWidget(self.export_report_btn)
        layout.addLayout(control_layout)

        self.report_preview = QPlainTextEdit()
        self.report_preview.setReadOnly(True)
        self.report_preview.setStyleSheet("""
            QPlainTextEdit {
                background-color: #2b2b36; color: #e2e8f0;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 14px; padding: 15px;
                border: 1px solid #3a3a48; border-radius: 6px;
            }
        """)
        self.report_preview.setPlainText("Нажмите «Сгенерировать сводный отчет», чтобы собрать данные из загруженного инвентаря и библиотеки игр.")
        layout.addWidget(self.report_preview)

        return page

    def display_page(self, index):
        self.pages.setCurrentIndex(index)

    # --- ЛОГИКА ИНВЕНТАРЯ ---
    def start_inventory_loading(self):
        steam_id = self.inv_steam_id_input.text().strip()
        if not steam_id:
            QMessageBox.warning(self, "Внимание", "Поле SteamID64 не должно быть пустым!")
            return
        self.last_used_steam_id = steam_id
        self.inv_analyze_btn.setEnabled(False)
        self.status_bar.showMessage("Запуск потока инвентаря...")
        self.inv_worker = InventoryFetchWorker(steam_id)
        self.inv_worker.status_update.connect(self.status_bar.showMessage)
        self.inv_worker.error.connect(self.handle_inv_error)
        self.inv_worker.finished.connect(self.handle_inv_success)
        self.inv_worker.start()

    def handle_inv_error(self, error_msg):
        QMessageBox.critical(self, "Ошибка инвентаря", error_msg)
        self.inv_analyze_btn.setEnabled(True)

    def handle_inv_success(self, inventory):
        self.current_inventory = inventory
        self.inv_analyze_btn.setEnabled(True)
        dist = InventoryAnalytics.calculate_distribution(inventory, "rarity")
        self.inv_chart_widget.update_pie_chart(dist, "Распределение инвентаря CS2 по редкости")
        self.apply_inventory_sorting()

    def apply_inventory_sorting(self):
        if not self.current_inventory: return
        display_items = self.current_inventory.copy()

        filter_idx = self.inv_filter_box.currentIndex()
        if filter_idx == 1: display_items = InventoryAnalytics.filter_items(display_items, lambda x: x.tradable)
        elif filter_idx == 2: display_items = InventoryAnalytics.filter_items(display_items, lambda x: x.marketable)

        sort_idx = self.inv_sort_box.currentIndex()
        if sort_idx == 1: display_items = InventoryAnalytics.merge_sort(display_items, key_extractor=lambda x: x.name, reverse=False)
        elif sort_idx == 2: display_items = InventoryAnalytics.merge_sort(display_items, key_extractor=lambda x: x.name, reverse=True)
        elif sort_idx == 3: display_items = InventoryAnalytics.merge_sort(display_items, key_extractor=lambda x: x.rarity, reverse=False)

        self.inv_table.setRowCount(0)
        self.inv_table.setRowCount(len(display_items))
        for row, item in enumerate(display_items):
            self.inv_table.setItem(row, 0, QTableWidgetItem(item.name))
            self.inv_table.setItem(row, 1, QTableWidgetItem(item.type))
            self.inv_table.setItem(row, 2, QTableWidgetItem(item.rarity))
            self.inv_table.setItem(row, 3, QTableWidgetItem(item.exterior))
            self.inv_table.setItem(row, 4, QTableWidgetItem(item.asset_id))

    # --- ЛОГИКА БИБЛИОТЕКИ ИГР ---
    def start_library_loading(self):
        steam_id = self.lib_steam_id_input.text().strip()
        if not steam_id:
            QMessageBox.warning(self, "Внимание", "Поле SteamID64 не должно быть пустым!")
            return
        self.last_used_steam_id = steam_id
        self.lib_analyze_btn.setEnabled(False)
        self.status_bar.showMessage("Запуск потока API библиотеки игр...")
        self.lib_worker = LibraryFetchWorker(steam_id)
        self.lib_worker.status_update.connect(self.status_bar.showMessage)
        self.lib_worker.error.connect(self.handle_lib_error)
        self.lib_worker.finished.connect(self.handle_lib_success)
        self.lib_worker.start()

    def handle_lib_error(self, error_msg):
        QMessageBox.critical(self, "Ошибка библиотеки", error_msg)
        self.lib_analyze_btn.setEnabled(True)

    def handle_lib_success(self, games):
        self.current_games = games
        self.lib_analyze_btn.setEnabled(True)

        summary = InventoryAnalytics.get_library_summary(games)
        self.lbl_total_games.setText(f"Всего игр: <b>{summary['total_games']}</b>")
        self.lbl_total_hours.setText(f"Общее время: <b>{summary['total_hours']} ч.</b>")
        self.lbl_top_game.setText(f"Главная игра: <b>{summary['top_game']}</b>")

        sorted_for_chart = InventoryAnalytics.merge_sort(games, key_extractor=lambda x: x.playtime_forever_hours, reverse=True)
        self.lib_chart_widget.update_bar_chart(sorted_for_chart[:5], "ТОП-5 игр по количеству часов")
        self.apply_library_sorting()

    def apply_library_sorting(self):
        if not self.current_games: return
        display_games = self.current_games.copy()

        sort_idx = self.lib_sort_box.currentIndex()
        if sort_idx == 1: display_games = InventoryAnalytics.merge_sort(display_games, key_extractor=lambda x: x.playtime_forever_hours, reverse=True)
        elif sort_idx == 2: display_games = InventoryAnalytics.merge_sort(display_games, key_extractor=lambda x: x.playtime_forever_hours, reverse=False)
        elif sort_idx == 3: display_games = InventoryAnalytics.merge_sort(display_games, key_extractor=lambda x: x.name, reverse=False)

        self.lib_table.setRowCount(0)
        self.lib_table.setRowCount(len(display_games))
        for row, game in enumerate(display_games):
            self.lib_table.setItem(row, 0, QTableWidgetItem(str(game.app_id)))
            self.lib_table.setItem(row, 1, QTableWidgetItem(game.name))
            self.lib_table.setItem(row, 2, QTableWidgetItem(f"{game.playtime_forever_hours:.1f}"))

    # --- ЛОГИКА АНАЛИЗА АККАУНТА ---
    def check_account_status(self):
        if not self.last_used_steam_id:
            QMessageBox.warning(self, "Нет SteamID", "Сначала введите SteamID во вкладке Инвентаря или Библиотеки!")
            return
        self.check_acc_btn.setEnabled(False)
        self.status_bar.showMessage("Проверка VAC и статуса аккаунта...")
        self.acc_worker = AccountFetchWorker(self.last_used_steam_id)
        self.acc_worker.finished.connect(self.handle_acc_success)
        self.acc_worker.error.connect(self.handle_acc_error)
        self.acc_worker.start()

    def handle_acc_success(self, status):
        self.check_acc_btn.setEnabled(True)
        url = f"https://steamcommunity.com/profiles/{status.steam_id}"
        self.lbl_acc_name.setText(f"Никнейм: <a href='{url}' style='color: #3b82f6; text-decoration: none;'><b>{status.persona_name}</b></a>")
        
        if status.avatar_bytes:
            img = QImage.fromData(status.avatar_bytes)
            pixmap = QPixmap.fromImage(img)
            self.lbl_avatar.setPixmap(pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        vac_text = f"<span style='color:red'>Да ({status.days_since_last_ban} дн. назад)</span>" if status.is_vac_banned else "<span style='color:#10b981'>Нет</span>"
        self.lbl_acc_vac.setText(f"VAC Бан: {vac_text}")
        
        comm_text = "<span style='color:red'>Заблокирован</span>" if status.is_community_banned else "<span style='color:#10b981'>Чист</span>"
        self.lbl_acc_comm.setText(f"Бан сообщества: {comm_text}")
        
        econ_text = "<span style='color:red'>Забанен</span>" if status.economy_ban != 'none' else "<span style='color:#10b981'>Разрешен</span>"
        self.lbl_acc_econ.setText(f"Трейд Бан: {econ_text}")
        
        self.status_bar.showMessage("Статус аккаунта успешно загружен.")

    def handle_acc_error(self, error_msg):
        self.check_acc_btn.setEnabled(True)
        QMessageBox.warning(self, "Ошибка", error_msg)

    # --- ЛОГИКА ОТЧЕТА И ЭКСПОРТА ---
    def generate_report(self):
        if not self.current_inventory and not self.current_games:
            QMessageBox.warning(self, "Нет данных", "Сначала загрузите инвентарь или библиотеку игр!")
            return
        report_text = ReportGenerator.build_summary_text(
            steam_id=self.last_used_steam_id,
            inventory=self.current_inventory,
            games=self.current_games
        )
        self.report_preview.setPlainText(report_text)
        self.export_report_btn.setEnabled(True)
        self.status_bar.showMessage("Сводный отчет успешно сгенерирован.")

    def export_report(self):
        content = self.report_preview.toPlainText()
        if not content: return
        filepath, _ = QFileDialog.getSaveFileName(self, "Сохранить отчет", f"Steam_Report_{self.last_used_steam_id}.txt", "Text Files (*.txt);;All Files (*)")
        if filepath:
            success = ReportGenerator.export_to_txt(filepath, content)
            if success:
                QMessageBox.information(self, "Успех", f"Отчет успешно сохранен:\n{filepath}")
                self.status_bar.showMessage(f"Файл сохранен: {filepath}")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось сохранить файл. Проверьте права доступа.")