# gui/charts.py
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QVBoxLayout, QWidget

class InventoryChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.figure.patch.set_facecolor('#1e1e24') 
        self.canvas = FigureCanvasQTAgg(self.figure)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#1e1e24')

    def update_pie_chart(self, distribution_data: dict, title: str):
        self.ax.clear()
        if not distribution_data:
            self.canvas.draw()
            return

        total = sum(distribution_data.values())
        new_labels = []
        new_sizes = []
        other_size = 0
        
        for label, size in distribution_data.items():
            if (size / total) * 100 < 3.0:
                other_size += size
            else:
                new_labels.append(label)
                new_sizes.append(size)
                
        if other_size > 0:
            new_labels.append("Прочее (< 3%)")
            new_sizes.append(other_size)

        colors = ['#b0c3d9', '#5e98d9', '#4b69ff', '#8847ff', '#d32ce6', '#eb4b4b', '#aaaaaa']
        
        wedges, texts, autotexts = self.ax.pie(
            new_sizes, 
            autopct='%1.1f%%', 
            startangle=140,
            colors=colors[:len(new_labels)], 
            textprops={'color': "#ffffff", 'fontsize': 10, 'fontweight': 'bold'}
        )
        
        self.ax.legend(wedges, new_labels, title="Редкость", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), labelcolor='white', facecolor='#2b2b36', edgecolor='#3a3a48')
        self.ax.set_title(title, color="#ffffff", pad=20, fontsize=14, fontweight='bold')
        self.ax.axis('equal') 
        self.figure.tight_layout()
        self.canvas.draw()


class LibraryChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(7, 4), dpi=100)
        self.figure.patch.set_facecolor('#1e1e24') 
        self.canvas = FigureCanvasQTAgg(self.figure)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#1e1e24')

    def update_bar_chart(self, top_games: list, title: str):
        self.ax.clear()
        if not top_games:
            self.canvas.draw()
            return

        names = [g.name for g in top_games]
        hours = [g.playtime_forever_hours for g in top_games]

        bars = self.ax.barh(names, hours, color='#3b82f6', height=0.6)
        
        self.ax.set_title(title, color="#ffffff", pad=15, fontsize=13, fontweight='bold')
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white', labelsize=11)
        self.ax.invert_yaxis()  
        
        for bar in bars:
            width = bar.get_width()
            self.ax.text(width + (width * 0.01 + 0.5), bar.get_y() + bar.get_height()/2,
                         f'{int(width)} ч.',
                         va='center', ha='left', color='white', fontsize=10, fontweight='bold')

        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['bottom'].set_color('#3a3a48')
        self.ax.spines['left'].set_color('#3a3a48')
        
        self.figure.tight_layout()
        self.canvas.draw()