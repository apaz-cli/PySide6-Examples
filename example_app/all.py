import sys
import random
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                               QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, 
                               QLabel, QLineEdit, QTextEdit, QSlider, QProgressBar,
                               QCheckBox, QRadioButton, QComboBox, QSpinBox,
                               QListWidget, QTableWidget, QTableWidgetItem,
                               QGroupBox, QButtonGroup, QMessageBox, QFileDialog,
                               QColorDialog, QFontDialog, QCalendarWidget,
                               QTreeWidget, QTreeWidgetItem, QSplitter, QScrollArea,
                               QTextBrowser, QPlainTextEdit, QToolBar)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QUrl
from PySide6.QtGui import (QPixmap, QPainter, QPen, QColor, QFont, QAction, 
                           QKeySequence, QDragEnterEvent, QDropEvent)
import math
import time

# Try to import optional components
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    WEB_ENGINE_AVAILABLE = True
except ImportError:
    WEB_ENGINE_AVAILABLE = False

try:
    from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PySide6.QtMultimediaWidgets import QVideoWidget
    MULTIMEDIA_AVAILABLE = True
except ImportError:
    MULTIMEDIA_AVAILABLE = False


class CalculatorTab(QWidget):
    """Simple calculator tab"""
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Display
        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignRight)
        self.display.setStyleSheet("font-size: 18px; padding: 10px;")
        layout.addWidget(self.display)
        
        # Buttons
        buttons_layout = QGridLayout()
        
        buttons = [
            ('C', 0, 0), ('±', 0, 1), ('%', 0, 2), ('÷', 0, 3),
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('×', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('-', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('+', 3, 3),
            ('0', 4, 0, 1, 2), ('.', 4, 2), ('=', 4, 3)
        ]
        
        for button_info in buttons:
            text = button_info[0]
            row = button_info[1]
            col = button_info[2]
            row_span = button_info[3] if len(button_info) > 3 else 1
            col_span = button_info[4] if len(button_info) > 4 else 1
            
            btn = QPushButton(text)
            btn.clicked.connect(lambda checked, t=text: self.button_clicked(t))
            btn.setMinimumHeight(50)
            buttons_layout.addWidget(btn, row, col, row_span, col_span)
        
        buttons_widget = QWidget()
        buttons_widget.setLayout(buttons_layout)
        layout.addWidget(buttons_widget)
        
        self.setLayout(layout)
        self.current_input = ""
        self.result = 0
        self.operator = ""
        self.waiting_for_operand = False
        
    def button_clicked(self, text):
        if text.isdigit() or text == '.':
            if self.waiting_for_operand:
                self.current_input = text
                self.waiting_for_operand = False
            else:
                self.current_input += text
            self.display.setText(self.current_input)
            
        elif text in ['+', '-', '×', '÷']:
            if self.current_input:
                if self.operator and not self.waiting_for_operand:
                    self.calculate()
                self.result = float(self.current_input)
                self.operator = text
                self.waiting_for_operand = True
                
        elif text == '=':
            self.calculate()
            
        elif text == 'C':
            self.current_input = ""
            self.result = 0
            self.operator = ""
            self.waiting_for_operand = False
            self.display.setText("0")
            
    def calculate(self):
        if self.operator and self.current_input:
            current_value = float(self.current_input)
            
            if self.operator == '+':
                self.result += current_value
            elif self.operator == '-':
                self.result -= current_value
            elif self.operator == '×':
                self.result *= current_value
            elif self.operator == '÷':
                if current_value != 0:
                    self.result /= current_value
                else:
                    QMessageBox.warning(self, "Error", "Cannot divide by zero!")
                    return
                    
            self.current_input = str(self.result)
            self.display.setText(self.current_input)
            self.operator = ""
            self.waiting_for_operand = True


class TodoTab(QWidget):
    """Todo list tab"""
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Input section
        input_layout = QHBoxLayout()
        self.todo_input = QLineEdit()
        self.todo_input.setPlaceholderText("Enter a new task...")
        self.todo_input.returnPressed.connect(self.add_todo)
        
        add_btn = QPushButton("Add Task")
        add_btn.clicked.connect(self.add_todo)
        
        input_layout.addWidget(self.todo_input)
        input_layout.addWidget(add_btn)
        
        layout.addLayout(input_layout)
        
        # Todo list
        self.todo_list = QListWidget()
        layout.addWidget(self.todo_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        complete_btn = QPushButton("Mark Complete")
        complete_btn.clicked.connect(self.mark_complete)
        
        delete_btn = QPushButton("Delete Task")
        delete_btn.clicked.connect(self.delete_task)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_all)
        
        button_layout.addWidget(complete_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addWidget(clear_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def add_todo(self):
        text = self.todo_input.text().strip()
        if text:
            self.todo_list.addItem(f"☐ {text}")
            self.todo_input.clear()
            
    def mark_complete(self):
        current_item = self.todo_list.currentItem()
        if current_item:
            text = current_item.text()
            if text.startswith("☐"):
                current_item.setText(text.replace("☐", "✓"))
            elif text.startswith("✓"):
                current_item.setText(text.replace("✓", "☐"))
                
    def delete_task(self):
        current_row = self.todo_list.currentRow()
        if current_row >= 0:
            self.todo_list.takeItem(current_row)
            
    def clear_all(self):
        reply = QMessageBox.question(self, "Clear All", "Are you sure you want to clear all tasks?")
        if reply == QMessageBox.Yes:
            self.todo_list.clear()


class DrawingTab(QWidget):
    """Simple drawing tab"""
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.drawing = False
        self.brush_size = 3
        self.brush_color = Qt.black
        self.last_point = None
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Brush size
        size_label = QLabel("Brush Size:")
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(1, 20)
        self.size_slider.setValue(3)
        self.size_slider.valueChanged.connect(self.change_brush_size)
        
        # Color button
        self.color_btn = QPushButton("Choose Color")
        self.color_btn.clicked.connect(self.choose_color)
        self.color_btn.setStyleSheet("background-color: black;")
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_canvas)
        
        controls_layout.addWidget(size_label)
        controls_layout.addWidget(self.size_slider)
        controls_layout.addWidget(self.color_btn)
        controls_layout.addWidget(clear_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Drawing area
        self.canvas = QLabel()
        self.canvas.setMinimumSize(600, 400)
        self.canvas.setStyleSheet("border: 1px solid black; background-color: white;")
        self.pixmap = QPixmap(600, 400)
        self.pixmap.fill(Qt.white)
        self.canvas.setPixmap(self.pixmap)
        
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
    def change_brush_size(self, value):
        self.brush_size = value
        
    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.brush_color = color
            self.color_btn.setStyleSheet(f"background-color: {color.name()};")
            
    def clear_canvas(self):
        self.pixmap.fill(Qt.white)
        self.canvas.setPixmap(self.pixmap)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.last_point = event.position().toPoint()
            
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.drawing:
            current_point = event.position().toPoint()
            
            painter = QPainter(self.pixmap)
            painter.setPen(QPen(self.brush_color, self.brush_size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            
            if self.last_point:
                painter.drawLine(self.last_point, current_point)
                
            self.last_point = current_point
            self.canvas.setPixmap(self.pixmap)
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False


class DataVisualizationTab(QWidget):
    """Data visualization with charts tab"""
    def __init__(self):
        super().__init__()
        self.data = []
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Controls
        controls_layout = QHBoxLayout()
        
        add_data_btn = QPushButton("Add Random Data")
        add_data_btn.clicked.connect(self.add_random_data)
        
        clear_btn = QPushButton("Clear Data")
        clear_btn.clicked.connect(self.clear_data)
        
        self.chart_type = QComboBox()
        self.chart_type.addItems(["Bar Chart", "Line Chart", "Pie Chart"])
        self.chart_type.currentTextChanged.connect(self.update_chart)
        
        controls_layout.addWidget(add_data_btn)
        controls_layout.addWidget(clear_btn)
        controls_layout.addWidget(QLabel("Chart Type:"))
        controls_layout.addWidget(self.chart_type)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Chart area
        self.chart_label = QLabel()
        self.chart_label.setMinimumSize(600, 400)
        self.chart_label.setStyleSheet("border: 1px solid black; background-color: white;")
        self.chart_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.chart_label)
        
        # Data table
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(2)
        self.data_table.setHorizontalHeaderLabels(["Label", "Value"])
        self.data_table.setMaximumHeight(150)
        
        layout.addWidget(self.data_table)
        self.setLayout(layout)
        
        self.update_chart()
        
    def add_random_data(self):
        labels = ["Item A", "Item B", "Item C", "Item D", "Item E"]
        if len(self.data) < len(labels):
            label = labels[len(self.data)]
            value = random.randint(10, 100)
            self.data.append((label, value))
            self.update_table()
            self.update_chart()
            
    def clear_data(self):
        self.data.clear()
        self.update_table()
        self.update_chart()
        
    def update_table(self):
        self.data_table.setRowCount(len(self.data))
        for i, (label, value) in enumerate(self.data):
            self.data_table.setItem(i, 0, QTableWidgetItem(label))
            self.data_table.setItem(i, 1, QTableWidgetItem(str(value)))
            
    def update_chart(self):
        if not self.data:
            self.chart_label.setText("Add some data to see the chart")
            return
            
        chart_type = self.chart_type.currentText()
        pixmap = QPixmap(580, 380)
        pixmap.fill(Qt.white)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if chart_type == "Bar Chart":
            self.draw_bar_chart(painter, pixmap.width(), pixmap.height())
        elif chart_type == "Line Chart":
            self.draw_line_chart(painter, pixmap.width(), pixmap.height())
        elif chart_type == "Pie Chart":
            self.draw_pie_chart(painter, pixmap.width(), pixmap.height())
            
        painter.end()
        self.chart_label.setPixmap(pixmap)
        
    def draw_bar_chart(self, painter, width, height):
        margin = 50
        chart_width = width - 2 * margin
        chart_height = height - 2 * margin
        
        max_value = max(value for _, value in self.data)
        bar_width = chart_width // len(self.data)
        
        colors = [Qt.red, Qt.blue, Qt.green, Qt.yellow, Qt.magenta]
        
        for i, (label, value) in enumerate(self.data):
            bar_height = (value / max_value) * chart_height
            x = margin + i * bar_width
            y = height - margin - bar_height
            
            painter.fillRect(x + 5, y, bar_width - 10, bar_height, colors[i % len(colors)])
            painter.drawText(x, height - margin + 20, label)
            
    def draw_line_chart(self, painter, width, height):
        margin = 50
        chart_width = width - 2 * margin
        chart_height = height - 2 * margin
        
        if len(self.data) < 2:
            return
            
        max_value = max(value for _, value in self.data)
        points = []
        
        for i, (_, value) in enumerate(self.data):
            x = margin + (i / (len(self.data) - 1)) * chart_width
            y = height - margin - (value / max_value) * chart_height
            points.append((x, y))
            
        painter.setPen(QPen(Qt.blue, 2))
        for i in range(len(points) - 1):
            painter.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
            
        for i, (x, y) in enumerate(points):
            painter.fillRect(x - 3, y - 3, 6, 6, Qt.red)
            painter.drawText(x - 20, height - margin + 20, self.data[i][0])
            
    def draw_pie_chart(self, painter, width, height):
        center_x = width // 2
        center_y = height // 2
        radius = min(width, height) // 3
        
        total = sum(value for _, value in self.data)
        start_angle = 0
        colors = [Qt.red, Qt.blue, Qt.green, Qt.yellow, Qt.magenta]
        
        for i, (label, value) in enumerate(self.data):
            span_angle = int((value / total) * 360 * 16)  # Qt uses 1/16th degrees
            painter.setBrush(colors[i % len(colors)])
            painter.drawPie(center_x - radius, center_y - radius, 
                          radius * 2, radius * 2, start_angle, span_angle)
            start_angle += span_angle


class SettingsTab(QWidget):
    """Settings and preferences tab"""
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Theme settings
        theme_group = QGroupBox("Theme Settings")
        theme_layout = QVBoxLayout()
        
        self.theme_group = QButtonGroup()
        light_radio = QRadioButton("Light Theme")
        dark_radio = QRadioButton("Dark Theme")
        light_radio.setChecked(True)
        
        self.theme_group.addButton(light_radio, 0)
        self.theme_group.addButton(dark_radio, 1)
        
        theme_layout.addWidget(light_radio)
        theme_layout.addWidget(dark_radio)
        theme_group.setLayout(theme_layout)
        
        # Font settings
        font_group = QGroupBox("Font Settings")
        font_layout = QGridLayout()
        
        font_layout.addWidget(QLabel("Font Size:"), 0, 0)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(12)
        font_layout.addWidget(self.font_size_spin, 0, 1)
        
        font_btn = QPushButton("Choose Font")
        font_btn.clicked.connect(self.choose_font)
        font_layout.addWidget(font_btn, 1, 0, 1, 2)
        
        font_group.setLayout(font_layout)
        
        # General settings
        general_group = QGroupBox("General Settings")
        general_layout = QVBoxLayout()
        
        self.auto_save_check = QCheckBox("Auto-save enabled")
        self.notifications_check = QCheckBox("Show notifications")
        self.sound_check = QCheckBox("Sound effects")
        
        self.auto_save_check.setChecked(True)
        self.notifications_check.setChecked(True)
        
        general_layout.addWidget(self.auto_save_check)
        general_layout.addWidget(self.notifications_check)
        general_layout.addWidget(self.sound_check)
        
        general_group.setLayout(general_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        apply_btn = QPushButton("Apply Settings")
        apply_btn.clicked.connect(self.apply_settings)
        
        reset_btn = QPushButton("Reset to Default")
        reset_btn.clicked.connect(self.reset_settings)
        
        button_layout.addWidget(apply_btn)
        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        
        # Add all to main layout
        layout.addWidget(theme_group)
        layout.addWidget(font_group)
        layout.addWidget(general_group)
        layout.addLayout(button_layout)
        layout.addStretch()
        
        self.setLayout(layout)
        
    def choose_font(self):
        font, ok = QFontDialog.getFont()
        if ok:
            QMessageBox.information(self, "Font Selected", f"Selected font: {font.family()}")
            
    def apply_settings(self):
        theme = "Light" if self.theme_group.checkedId() == 0 else "Dark"
        font_size = self.font_size_spin.value()
        auto_save = self.auto_save_check.isChecked()
        notifications = self.notifications_check.isChecked()
        sound = self.sound_check.isChecked()
        
        settings_text = f"""Settings Applied:
Theme: {theme}
Font Size: {font_size}
Auto-save: {auto_save}
Notifications: {notifications}
Sound Effects: {sound}"""
        
        QMessageBox.information(self, "Settings Applied", settings_text)
        
    def reset_settings(self):
        self.theme_group.button(0).setChecked(True)
        self.font_size_spin.setValue(12)
        self.auto_save_check.setChecked(True)
        self.notifications_check.setChecked(True)
        self.sound_check.setChecked(False)
        QMessageBox.information(self, "Settings Reset", "All settings have been reset to default values.")


class HTMLRenderTab(QWidget):
    """HTML rendering with CSS styling tab"""
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Controls
        controls_layout = QHBoxLayout()
        
        load_btn = QPushButton("Load HTML File")
        load_btn.clicked.connect(self.load_html_file)
        
        reload_btn = QPushButton("Reload")
        reload_btn.clicked.connect(self.reload_content)
        
        sample_btn = QPushButton("Load Sample HTML")
        sample_btn.clicked.connect(self.load_sample_html)
        
        controls_layout.addWidget(load_btn)
        controls_layout.addWidget(reload_btn)
        controls_layout.addWidget(sample_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Splitter for HTML input and rendered output
        splitter = QSplitter(Qt.Horizontal)
        
        # HTML input area
        input_widget = QWidget()
        input_layout = QVBoxLayout()
        input_layout.addWidget(QLabel("HTML + CSS Code:"))
        
        self.html_input = QPlainTextEdit()
        self.html_input.setPlainText(self.get_sample_html())
        self.html_input.textChanged.connect(self.update_preview)
        
        input_layout.addWidget(self.html_input)
        input_widget.setLayout(input_layout)
        
        # Web view for rendering
        preview_widget = QWidget()
        preview_layout = QVBoxLayout()
        preview_layout.addWidget(QLabel("Rendered Output:"))
        
        if WEB_ENGINE_AVAILABLE:
            self.web_view = QWebEngineView()
        else:
            # Fallback to QTextBrowser if WebEngine is not available
            self.web_view = QTextBrowser()
            
        preview_layout.addWidget(self.web_view)
        preview_widget.setLayout(preview_layout)
        
        splitter.addWidget(input_widget)
        splitter.addWidget(preview_widget)
        splitter.setSizes([400, 400])
        
        layout.addWidget(splitter)
        self.setLayout(layout)
        
        # Initial load
        self.update_preview()
        
    def get_sample_html(self):
        return """<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            color: white;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        .card {
            background: rgba(255, 255, 255, 0.2);
            padding: 20px;
            margin: 15px 0;
            border-radius: 10px;
            border-left: 4px solid #ff6b6b;
            transition: transform 0.3s ease;
        }
        .card:hover {
            transform: translateY(-5px);
        }
        .btn {
            background: #ff6b6b;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .btn:hover {
            background: #ff5252;
            transform: scale(1.05);
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .grid-item {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 Modern CSS Demo</h1>
        
        <div class="card">
            <h3>Welcome to the HTML/CSS Renderer!</h3>
            <p>This tab demonstrates modern CSS features including gradients, 
               glassmorphism effects, transitions, and grid layouts.</p>
            <button class="btn">Interactive Button</button>
        </div>
        
        <div class="card">
            <h3>Features Showcase</h3>
            <div class="grid">
                <div class="grid-item">
                    <h4>🌈 Gradients</h4>
                    <p>Beautiful color transitions</p>
                </div>
                <div class="grid-item">
                    <h4>✨ Glassmorphism</h4>
                    <p>Frosted glass effects</p>
                </div>
                <div class="grid-item">
                    <h4>🎭 Animations</h4>
                    <p>Smooth transitions</p>
                </div>
                <div class="grid-item">
                    <h4>📱 Responsive</h4>
                    <p>Grid auto-layout</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""
        
    def update_preview(self):
        html_content = self.html_input.toPlainText()
        self.web_view.setHtml(html_content)
            
    def load_html_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open HTML File", "", "HTML Files (*.html *.htm);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    self.html_input.setPlainText(content)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not load file: {str(e)}")
                
    def reload_content(self):
        self.update_preview()
        
    def load_sample_html(self):
        self.html_input.setPlainText(self.get_sample_html())


class TextEditorTab(QWidget):
    """Text editor with formatting options"""
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        # File operations
        new_btn = QPushButton("New")
        new_btn.clicked.connect(self.new_file)
        
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self.open_file)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_file)
        
        save_as_btn = QPushButton("Save As")
        save_as_btn.clicked.connect(self.save_as_file)
        
        # Font controls
        font_combo = QComboBox()
        font_combo.addItems(["Arial", "Times New Roman", "Courier New", "Helvetica"])
        font_combo.currentTextChanged.connect(self.change_font_family)
        
        font_size_combo = QComboBox()
        font_size_combo.addItems(["8", "10", "12", "14", "16", "18", "20", "24", "28", "32"])
        font_size_combo.setCurrentText("12")
        font_size_combo.currentTextChanged.connect(self.change_font_size)
        
        toolbar_layout.addWidget(new_btn)
        toolbar_layout.addWidget(open_btn)
        toolbar_layout.addWidget(save_btn)
        toolbar_layout.addWidget(save_as_btn)
        toolbar_layout.addWidget(QLabel("Font:"))
        toolbar_layout.addWidget(font_combo)
        toolbar_layout.addWidget(QLabel("Size:"))
        toolbar_layout.addWidget(font_size_combo)
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # Text editor
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText("Welcome to the Text Editor!\n\nStart typing your content here...")
        layout.addWidget(self.text_edit)
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # Connect text change signal
        self.text_edit.textChanged.connect(self.text_changed)
        
    def new_file(self):
        if self.text_edit.document().isModified():
            reply = QMessageBox.question(self, "Unsaved Changes", 
                                       "Do you want to save your changes?",
                                       QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                self.save_file()
            elif reply == QMessageBox.Cancel:
                return
                
        self.text_edit.clear()
        self.current_file = None
        self.status_label.setText("New document")
        
    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    self.text_edit.setPlainText(content)
                    self.current_file = file_path
                    self.status_label.setText(f"Opened: {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not open file: {str(e)}")
                
    def save_file(self):
        if self.current_file:
            self.save_to_file(self.current_file)
        else:
            self.save_as_file()
            
    def save_as_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", "", "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            self.save_to_file(file_path)
            self.current_file = file_path
            
    def save_to_file(self, file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(self.text_edit.toPlainText())
                self.text_edit.document().setModified(False)
                self.status_label.setText(f"Saved: {os.path.basename(file_path)}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save file: {str(e)}")
            
    def change_font_family(self, family):
        font = self.text_edit.font()
        font.setFamily(family)
        self.text_edit.setFont(font)
        
    def change_font_size(self, size):
        font = self.text_edit.font()
        font.setPointSize(int(size))
        self.text_edit.setFont(font)
        
    def text_changed(self):
        if self.current_file:
            status = f"Modified: {os.path.basename(self.current_file)}"
        else:
            status = "Modified"
        self.status_label.setText(status)


class ImageViewerTab(QWidget):
    """Drag and drop image viewer"""
    def __init__(self):
        super().__init__()
        self.current_image = None
        self.scale_factor = 1.0
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Controls
        controls_layout = QHBoxLayout()
        
        open_btn = QPushButton("Open Image")
        open_btn.clicked.connect(self.open_image)
        
        zoom_in_btn = QPushButton("Zoom In")
        zoom_in_btn.clicked.connect(self.zoom_in)
        
        zoom_out_btn = QPushButton("Zoom Out")
        zoom_out_btn.clicked.connect(self.zoom_out)
        
        fit_btn = QPushButton("Fit to Window")
        fit_btn.clicked.connect(self.fit_to_window)
        
        reset_btn = QPushButton("Reset Zoom")
        reset_btn.clicked.connect(self.reset_zoom)
        
        controls_layout.addWidget(open_btn)
        controls_layout.addWidget(zoom_in_btn)
        controls_layout.addWidget(zoom_out_btn)
        controls_layout.addWidget(fit_btn)
        controls_layout.addWidget(reset_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Image display area
        self.scroll_area = QScrollArea()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                background-color: #f0f0f0;
                color: #666;
                font-size: 14px;
            }
        """)
        self.image_label.setText("Drag and drop an image here\nor click 'Open Image' to browse")
        self.image_label.setMinimumSize(400, 300)
        
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setWidgetResizable(True)
        
        layout.addWidget(self.scroll_area)
        
        # Status
        self.status_label = QLabel("No image loaded")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')):
                    event.acceptProposedAction()
                    
    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            file_path = urls[0].toLocalFile()
            self.load_image(file_path)
            
    def open_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", 
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp *.tiff);;All Files (*)"
        )
        if file_path:
            self.load_image(file_path)
            
    def load_image(self, file_path):
        try:
            self.current_image = QPixmap(file_path)
            if self.current_image.isNull():
                QMessageBox.warning(self, "Error", "Could not load image file")
                return
                
            self.scale_factor = 1.0
            self.update_image_display()
            self.status_label.setText(f"Loaded: {os.path.basename(file_path)} "
                                    f"({self.current_image.width()}x{self.current_image.height()})")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load image: {str(e)}")
            
    def update_image_display(self):
        if self.current_image:
            scaled_image = self.current_image.scaled(
                self.current_image.size() * self.scale_factor,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_image)
            self.image_label.resize(scaled_image.size())
            
    def zoom_in(self):
        if self.current_image:
            self.scale_factor *= 1.25
            self.update_image_display()
            
    def zoom_out(self):
        if self.current_image:
            self.scale_factor /= 1.25
            self.update_image_display()
            
    def fit_to_window(self):
        if self.current_image:
            scroll_size = self.scroll_area.size()
            image_size = self.current_image.size()
            
            scale_x = scroll_size.width() / image_size.width()
            scale_y = scroll_size.height() / image_size.height()
            self.scale_factor = min(scale_x, scale_y) * 0.9  # 90% to leave some margin
            
            self.update_image_display()
            
    def reset_zoom(self):
        if self.current_image:
            self.scale_factor = 1.0
            self.update_image_display()


class MediaPlayerTab(QWidget):
    """File chooser and media player"""
    def __init__(self):
        super().__init__()
        if MULTIMEDIA_AVAILABLE:
            self.media_player = QMediaPlayer()
            self.audio_output = QAudioOutput()
            self.media_player.setAudioOutput(self.audio_output)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        if not MULTIMEDIA_AVAILABLE:
            layout.addWidget(QLabel("Multimedia components not available.\nInstall PySide6-Addons for media support."))
            self.setLayout(layout)
            return
        
        # File selection
        file_layout = QHBoxLayout()
        
        self.file_label = QLabel("No file selected")
        choose_file_btn = QPushButton("Choose Media File")
        choose_file_btn.clicked.connect(self.choose_file)
        
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(choose_file_btn)
        
        layout.addLayout(file_layout)
        
        # Video widget (for video files)
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(300)
        self.media_player.setVideoOutput(self.video_widget)
        layout.addWidget(self.video_widget)
        
        # Media controls
        controls_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self.play_pause)
        self.play_btn.setEnabled(False)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop)
        self.stop_btn.setEnabled(False)
        
        # Volume control
        volume_label = QLabel("Volume:")
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)
        
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(volume_label)
        controls_layout.addWidget(self.volume_slider)
        
        layout.addLayout(controls_layout)
        
        # Position slider
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.set_position)
        layout.addWidget(self.position_slider)
        
        # Status
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # Connect media player signals
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.playbackStateChanged.connect(self.state_changed)
        
        # Set initial volume
        self.set_volume(50)
        
    def choose_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Choose Media File", "",
            "Media Files (*.mp4 *.avi *.mov *.mp3 *.wav *.flac *.ogg);;All Files (*)"
        )
        if file_path:
            self.load_file(file_path)
            
    def load_file(self, file_path):
        try:
            self.media_player.setSource(QUrl.fromLocalFile(file_path))
            self.file_label.setText(f"File: {os.path.basename(file_path)}")
            self.play_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.status_label.setText(f"Loaded: {os.path.basename(file_path)}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load media file: {str(e)}")
            
    def play_pause(self):
        if self.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()
            
    def stop(self):
        self.media_player.stop()
        
    def set_volume(self, volume):
        self.audio_output.setVolume(volume / 100.0)
        
    def set_position(self, position):
        self.media_player.setPosition(position)
        
    def position_changed(self, position):
        self.position_slider.setValue(position)
        
    def duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
        
    def state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_btn.setText("Pause")
            self.status_label.setText("Playing")
        elif state == QMediaPlayer.PausedState:
            self.play_btn.setText("Play")
            self.status_label.setText("Paused")
        else:
            self.play_btn.setText("Play")
            self.status_label.setText("Stopped")


class NotificationTab(QWidget):
    """Desktop notification demonstration"""
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Desktop Notifications")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # Notification customization
        form_layout = QGridLayout()
        
        form_layout.addWidget(QLabel("Title:"), 0, 0)
        self.title_input = QLineEdit("Hello from PySide6!")
        form_layout.addWidget(self.title_input, 0, 1)
        
        form_layout.addWidget(QLabel("Message:"), 1, 0)
        self.message_input = QTextEdit()
        self.message_input.setPlainText("This is a desktop notification sent from your PySide6 application!")
        self.message_input.setMaximumHeight(100)
        form_layout.addWidget(self.message_input, 1, 1)
        
        form_layout.addWidget(QLabel("Icon:"), 2, 0)
        self.icon_combo = QComboBox()
        self.icon_combo.addItems(["Information", "Warning", "Critical", "Question"])
        form_layout.addWidget(self.icon_combo, 2, 1)
        
        form_widget = QWidget()
        form_widget.setLayout(form_layout)
        layout.addWidget(form_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        simple_btn = QPushButton("Send Simple Notification")
        simple_btn.clicked.connect(self.send_simple_notification)
        
        custom_btn = QPushButton("Send Custom Notification")
        custom_btn.clicked.connect(self.send_custom_notification)
        
        button_layout.addWidget(simple_btn)
        button_layout.addWidget(custom_btn)
        
        layout.addLayout(button_layout)
        
        # Examples
        examples_group = QGroupBox("Notification Examples")
        examples_layout = QVBoxLayout()
        
        info_btn = QPushButton("Information Notification")
        info_btn.clicked.connect(lambda: self.send_example_notification("info"))
        
        warning_btn = QPushButton("Warning Notification")
        warning_btn.clicked.connect(lambda: self.send_example_notification("warning"))
        
        error_btn = QPushButton("Error Notification")
        error_btn.clicked.connect(lambda: self.send_example_notification("error"))
        
        success_btn = QPushButton("Success Notification")
        success_btn.clicked.connect(lambda: self.send_example_notification("success"))
        
        examples_layout.addWidget(info_btn)
        examples_layout.addWidget(warning_btn)
        examples_layout.addWidget(error_btn)
        examples_layout.addWidget(success_btn)
        
        examples_group.setLayout(examples_layout)
        layout.addWidget(examples_group)
        
        # Info text
        info_text = QLabel("""
Note: Desktop notifications may require system permissions.
The appearance and behavior of notifications depends on your operating system.
        """)
        info_text.setStyleSheet("color: #666; font-style: italic; margin: 10px;")
        info_text.setWordWrap(True)
        layout.addWidget(info_text)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def send_simple_notification(self):
        QMessageBox.information(self, "Notification", "This is a simple notification!")
        
    def send_custom_notification(self):
        title = self.title_input.text() or "Notification"
        message = self.message_input.toPlainText() or "Custom notification message"
        icon_type = self.icon_combo.currentText()
        
        if icon_type == "Information":
            QMessageBox.information(self, title, message)
        elif icon_type == "Warning":
            QMessageBox.warning(self, title, message)
        elif icon_type == "Critical":
            QMessageBox.critical(self, title, message)
        elif icon_type == "Question":
            QMessageBox.question(self, title, message)
            
    def send_example_notification(self, notification_type):
        if notification_type == "info":
            QMessageBox.information(self, "Information", "This is an information message.")
        elif notification_type == "warning":
            QMessageBox.warning(self, "Warning", "This is a warning message.")
        elif notification_type == "error":
            QMessageBox.critical(self, "Error", "This is an error message.")
        elif notification_type == "success":
            QMessageBox.information(self, "Success", "Operation completed successfully!")


class MultiTabApp(QMainWindow):
    """Main application window with multiple tabs"""
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("PySide6 Multi-Tab Example Application")
        self.setGeometry(100, 100, 900, 700)
        
        # Create central widget and tab widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Add tabs
        self.tab_widget.addTab(CalculatorTab(), "Calculator")
        self.tab_widget.addTab(TodoTab(), "Todo List")
        self.tab_widget.addTab(DrawingTab(), "Drawing")
        self.tab_widget.addTab(DataVisualizationTab(), "Charts")
        self.tab_widget.addTab(SettingsTab(), "Settings")
        self.tab_widget.addTab(HTMLRenderTab(), "HTML Renderer")
        self.tab_widget.addTab(TextEditorTab(), "Text Editor")
        self.tab_widget.addTab(ImageViewerTab(), "Image Viewer")
        self.tab_widget.addTab(MediaPlayerTab(), "Media Player")
        self.tab_widget.addTab(NotificationTab(), "Notifications")
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self.tab_changed)
        
    def tab_changed(self, index):
        tab_names = ["Calculator", "Todo List", "Drawing", "Charts", "Settings", 
                    "HTML Renderer", "Text Editor", "Image Viewer", "Media Player", "Notifications"]
        if index < len(tab_names):
            self.statusBar().showMessage(f"Current tab: {tab_names[index]}")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PySide6 Multi-Tab Example")
    
    window = MultiTabApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()