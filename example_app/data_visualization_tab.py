"""
Data Visualization Tab - Create and display simple charts
"""

import random
import math
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QComboBox, QTableWidget, QTableWidgetItem,
                               QMessageBox, QSpinBox, QLineEdit)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QFont


class DataVisualizationTab(QWidget):
    """Data visualization tab with interactive charts"""
    
    def __init__(self):
        super().__init__()
        self.data = []
        self.init_ui()
        
    def init_ui(self):
        """Initialize the data visualization interface"""
        layout = QVBoxLayout()
        
        # Controls section
        controls_layout = QHBoxLayout()
        
        # Data controls
        add_data_btn = QPushButton("Add Random Data")
        add_data_btn.clicked.connect(self.add_random_data)
        add_data_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        
        add_custom_btn = QPushButton("Add Custom Data")
        add_custom_btn.clicked.connect(self.add_custom_data)
        add_custom_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 8px;")
        
        clear_btn = QPushButton("Clear Data")
        clear_btn.clicked.connect(self.clear_data)
        clear_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 8px;")
        
        # Chart type selector
        self.chart_type = QComboBox()
        self.chart_type.addItems(["Bar Chart", "Line Chart", "Pie Chart", "Scatter Plot"])
        self.chart_type.currentTextChanged.connect(self.update_chart)
        
        controls_layout.addWidget(add_data_btn)
        controls_layout.addWidget(add_custom_btn)
        controls_layout.addWidget(clear_btn)
        controls_layout.addWidget(QLabel("Chart Type:"))
        controls_layout.addWidget(self.chart_type)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Custom data input section (initially hidden)
        self.custom_input_layout = QHBoxLayout()
        self.label_input = QLineEdit()
        self.label_input.setPlaceholderText("Label")
        self.value_input = QSpinBox()
        self.value_input.setRange(1, 1000)
        self.value_input.setValue(50)
        
        add_custom_confirm_btn = QPushButton("Add")
        add_custom_confirm_btn.clicked.connect(self.confirm_custom_data)
        
        self.custom_input_layout.addWidget(QLabel("Label:"))
        self.custom_input_layout.addWidget(self.label_input)
        self.custom_input_layout.addWidget(QLabel("Value:"))
        self.custom_input_layout.addWidget(self.value_input)
        self.custom_input_layout.addWidget(add_custom_confirm_btn)
        self.custom_input_layout.addStretch()
        
        # Initially hide custom input
        self.custom_input_widget = QWidget()
        self.custom_input_widget.setLayout(self.custom_input_layout)
        self.custom_input_widget.hide()
        layout.addWidget(self.custom_input_widget)
        
        # Chart area
        self.chart_label = QLabel()
        self.chart_label.setMinimumSize(700, 450)
        self.chart_label.setStyleSheet("border: 1px solid #333; background-color: white;")
        self.chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.chart_label)
        
        # Data table
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(2)
        self.data_table.setHorizontalHeaderLabels(["Label", "Value"])
        self.data_table.setMaximumHeight(150)
        self.data_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                font-weight: bold;
                padding: 5px;
            }
        """)
        
        layout.addWidget(self.data_table)
        self.setLayout(layout)
        
        # Initialize with sample data
        self.add_sample_data()
        self.update_chart()
        
    def add_sample_data(self):
        """Add some sample data for demonstration"""
        sample_data = [
            ("Sales", 85),
            ("Marketing", 45),
            ("Development", 70)
        ]
        self.data.extend(sample_data)
        self.update_table()
        
    def add_random_data(self):
        """Add a random data point"""
        labels = ["Product A", "Product B", "Product C", "Product D", "Product E", 
                 "Service X", "Service Y", "Category 1", "Category 2", "Category 3"]
        
        if len(self.data) < len(labels):
            available_labels = [label for label in labels 
                              if label not in [item[0] for item in self.data]]
            if available_labels:
                label = random.choice(available_labels)
                value = random.randint(10, 100)
                self.data.append((label, value))
                self.update_table()
                self.update_chart()
        else:
            QMessageBox.information(self, "Data Limit", "Maximum number of data points reached.")
            
    def add_custom_data(self):
        """Show custom data input"""
        if self.custom_input_widget.isVisible():
            self.custom_input_widget.hide()
        else:
            self.custom_input_widget.show()
            self.label_input.setFocus()
            
    def confirm_custom_data(self):
        """Add custom data point"""
        label = self.label_input.text().strip()
        value = self.value_input.value()
        
        if not label:
            QMessageBox.warning(self, "Invalid Input", "Please enter a label.")
            return
            
        # Check for duplicate labels
        if any(item[0] == label for item in self.data):
            QMessageBox.warning(self, "Duplicate Label", "This label already exists.")
            return
            
        self.data.append((label, value))
        self.update_table()
        self.update_chart()
        
        # Clear inputs
        self.label_input.clear()
        self.value_input.setValue(50)
        self.custom_input_widget.hide()
        
    def clear_data(self):
        """Clear all data"""
        if not self.data:
            QMessageBox.information(self, "No Data", "There is no data to clear.")
            return
            
        reply = QMessageBox.question(
            self, "Clear Data", 
            "Are you sure you want to clear all data?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.data.clear()
            self.update_table()
            self.update_chart()
            
    def update_table(self):
        """Update the data table"""
        self.data_table.setRowCount(len(self.data))
        for i, (label, value) in enumerate(self.data):
            self.data_table.setItem(i, 0, QTableWidgetItem(label))
            self.data_table.setItem(i, 1, QTableWidgetItem(str(value)))
            
    def update_chart(self):
        """Update the chart display"""
        if not self.data:
            self.chart_label.setText("Add some data to see the chart\n\nClick 'Add Random Data' or 'Add Custom Data' to get started")
            return
            
        chart_type = self.chart_type.currentText()
        pixmap = QPixmap(680, 430)
        pixmap.fill(Qt.GlobalColor.white)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        try:
            if chart_type == "Bar Chart":
                self.draw_bar_chart(painter, pixmap.width(), pixmap.height())
            elif chart_type == "Line Chart":
                self.draw_line_chart(painter, pixmap.width(), pixmap.height())
            elif chart_type == "Pie Chart":
                self.draw_pie_chart(painter, pixmap.width(), pixmap.height())
            elif chart_type == "Scatter Plot":
                self.draw_scatter_plot(painter, pixmap.width(), pixmap.height())
        except Exception as e:
            painter.setPen(QPen(Qt.GlobalColor.red))
            painter.drawText(50, 50, f"Error drawing chart: {str(e)}")
            
        painter.end()
        self.chart_label.setPixmap(pixmap)
        
    def draw_bar_chart(self, painter, width, height):
        """Draw a bar chart"""
        margin = 60
        chart_width = width - 2 * margin
        chart_height = height - 2 * margin
        
        max_value = max(value for _, value in self.data)
        bar_width = chart_width // len(self.data)
        
        colors = [QColor("#FF6B6B"), QColor("#4ECDC4"), QColor("#45B7D1"), 
                 QColor("#96CEB4"), QColor("#FFEAA7"), QColor("#DDA0DD"),
                 QColor("#98D8C8"), QColor("#F7DC6F"), QColor("#BB8FCE")]
        
        # Draw title
        painter.setPen(QPen(Qt.GlobalColor.black))
        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        painter.drawText(width//2 - 50, 30, "Bar Chart")
        
        # Draw bars
        for i, (label, value) in enumerate(self.data):
            bar_height = (value / max_value) * chart_height
            x = margin + i * bar_width
            y = height - margin - bar_height
            
            color = colors[i % len(colors)]
            painter.fillRect(x + 5, y, bar_width - 10, bar_height, color)
            
            # Draw value on top of bar
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.setFont(QFont("Arial", 10))
            painter.drawText(x + bar_width//2 - 10, y - 5, str(value))
            
            # Draw label
            painter.save()
            painter.translate(x + bar_width//2, height - margin + 40)
            painter.rotate(-45)
            painter.drawText(-len(label) * 3, 0, label)
            painter.restore()
            
    def draw_line_chart(self, painter, width, height):
        """Draw a line chart"""
        margin = 60
        chart_width = width - 2 * margin
        chart_height = height - 2 * margin
        
        if len(self.data) < 2:
            painter.setPen(QPen(Qt.GlobalColor.red))
            painter.drawText(width//2 - 100, height//2, "Need at least 2 data points for line chart")
            return
            
        max_value = max(value for _, value in self.data)
        points = []
        
        # Draw title
        painter.setPen(QPen(Qt.GlobalColor.black))
        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        painter.drawText(width//2 - 50, 30, "Line Chart")
        
        # Calculate points
        for i, (_, value) in enumerate(self.data):
            x = margin + (i / (len(self.data) - 1)) * chart_width
            y = height - margin - (value / max_value) * chart_height
            points.append((x, y))
            
        # Draw line
        painter.setPen(QPen(QColor("#4ECDC4"), 3))
        for i in range(len(points) - 1):
            painter.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
            
        # Draw points and labels
        painter.setPen(QPen(Qt.GlobalColor.black))
        painter.setFont(QFont("Arial", 10))
        for i, ((x, y), (label, value)) in enumerate(zip(points, self.data)):
            painter.fillRect(x - 4, y - 4, 8, 8, QColor("#FF6B6B"))
            painter.drawText(x - 10, y - 10, str(value))
            
            # Draw label
            painter.save()
            painter.translate(x, height - margin + 40)
            painter.rotate(-45)
            painter.drawText(-len(label) * 3, 0, label)
            painter.restore()
            
    def draw_pie_chart(self, painter, width, height):
        """Draw a pie chart"""
        center_x = width // 2
        center_y = height // 2
        radius = min(width, height) // 3
        
        total = sum(value for _, value in self.data)
        start_angle = 0
        colors = [QColor("#FF6B6B"), QColor("#4ECDC4"), QColor("#45B7D1"), 
                 QColor("#96CEB4"), QColor("#FFEAA7"), QColor("#DDA0DD"),
                 QColor("#98D8C8"), QColor("#F7DC6F"), QColor("#BB8FCE")]
        
        # Draw title
        painter.setPen(QPen(Qt.GlobalColor.black))
        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        painter.drawText(width//2 - 50, 30, "Pie Chart")
        
        # Draw pie slices
        for i, (label, value) in enumerate(self.data):
            span_angle = int((value / total) * 360 * 16)  # Qt uses 1/16th degrees
            color = colors[i % len(colors)]
            painter.setBrush(color)
            painter.setPen(QPen(Qt.GlobalColor.white, 2))
            painter.drawPie(center_x - radius, center_y - radius, 
                          radius * 2, radius * 2, start_angle, span_angle)
            
            # Draw percentage label
            mid_angle = (start_angle + span_angle // 2) / 16.0  # Convert back to degrees
            mid_angle_rad = math.radians(mid_angle)
            label_x = center_x + (radius * 0.7) * math.cos(mid_angle_rad)
            label_y = center_y + (radius * 0.7) * math.sin(mid_angle_rad)
            
            percentage = (value / total) * 100
            painter.setPen(QPen(Qt.GlobalColor.white))
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(label_x - 15, label_y, f"{percentage:.1f}%")
            
            start_angle += span_angle
            
        # Draw legend
        legend_y = height - 100
        for i, (label, value) in enumerate(self.data):
            color = colors[i % len(colors)]
            legend_x = 20
            legend_item_y = legend_y + i * 20
            
            painter.fillRect(legend_x, legend_item_y, 15, 15, color)
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.setFont(QFont("Arial", 10))
            painter.drawText(legend_x + 20, legend_item_y + 12, f"{label}: {value}")
            
    def draw_scatter_plot(self, painter, width, height):
        """Draw a scatter plot"""
        margin = 60
        chart_width = width - 2 * margin
        chart_height = height - 2 * margin
        
        max_value = max(value for _, value in self.data)
        
        # Draw title
        painter.setPen(QPen(Qt.GlobalColor.black))
        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        painter.drawText(width//2 - 60, 30, "Scatter Plot")
        
        # Draw axes
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.drawLine(margin, height - margin, width - margin, height - margin)  # X-axis
        painter.drawLine(margin, margin, margin, height - margin)  # Y-axis
        
        # Draw points
        colors = [QColor("#FF6B6B"), QColor("#4ECDC4"), QColor("#45B7D1"), 
                 QColor("#96CEB4"), QColor("#FFEAA7")]
        
        for i, (label, value) in enumerate(self.data):
            x = margin + (i / len(self.data)) * chart_width
            y = height - margin - (value / max_value) * chart_height
            
            color = colors[i % len(colors)]
            painter.setBrush(color)
            painter.setPen(QPen(Qt.GlobalColor.black, 1))
            painter.drawEllipse(x - 8, y - 8, 16, 16)
            
            # Draw label
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.setFont(QFont("Arial", 9))
            painter.drawText(x - len(label) * 3, y + 25, label)