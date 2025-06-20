"""
Drawing Tab - Simple drawing canvas with brush tools
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QSlider, QColorDialog, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor


class DrawingTab(QWidget):
    """Simple drawing tab with brush tools and color selection"""
    
    def __init__(self):
        super().__init__()
        self.drawing = False
        self.brush_size = 3
        self.brush_color = Qt.GlobalColor.black
        self.last_point = QPoint()
        self.init_ui()
        
    def init_ui(self):
        """Initialize the drawing interface"""
        layout = QVBoxLayout()
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Brush size
        size_label = QLabel("Brush Size:")
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(1, 50)
        self.size_slider.setValue(3)
        self.size_slider.valueChanged.connect(self.change_brush_size)
        
        self.size_display = QLabel("3")
        self.size_display.setMinimumWidth(30)
        
        # Color button
        self.color_btn = QPushButton("Choose Color")
        self.color_btn.clicked.connect(self.choose_color)
        self.color_btn.setStyleSheet("background-color: black; color: white; font-weight: bold; padding: 8px;")
        
        # Preset colors
        red_btn = QPushButton()
        red_btn.setStyleSheet("background-color: red; min-width: 30px; min-height: 30px;")
        red_btn.clicked.connect(lambda: self.set_color(Qt.GlobalColor.red))
        
        green_btn = QPushButton()
        green_btn.setStyleSheet("background-color: green; min-width: 30px; min-height: 30px;")
        green_btn.clicked.connect(lambda: self.set_color(Qt.GlobalColor.green))
        
        blue_btn = QPushButton()
        blue_btn.setStyleSheet("background-color: blue; min-width: 30px; min-height: 30px;")
        blue_btn.clicked.connect(lambda: self.set_color(Qt.GlobalColor.blue))
        
        black_btn = QPushButton()
        black_btn.setStyleSheet("background-color: black; min-width: 30px; min-height: 30px;")
        black_btn.clicked.connect(lambda: self.set_color(Qt.GlobalColor.black))
        
        # Action buttons
        clear_btn = QPushButton("Clear Canvas")
        clear_btn.clicked.connect(self.clear_canvas)
        clear_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 8px;")
        
        save_btn = QPushButton("Save Image")
        save_btn.clicked.connect(self.save_image)
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        
        load_btn = QPushButton("Load Image")
        load_btn.clicked.connect(self.load_image)
        load_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 8px;")
        
        controls_layout.addWidget(size_label)
        controls_layout.addWidget(self.size_slider)
        controls_layout.addWidget(self.size_display)
        controls_layout.addWidget(QLabel("|"))
        controls_layout.addWidget(self.color_btn)
        controls_layout.addWidget(red_btn)
        controls_layout.addWidget(green_btn)
        controls_layout.addWidget(blue_btn)
        controls_layout.addWidget(black_btn)
        controls_layout.addWidget(QLabel("|"))
        controls_layout.addWidget(clear_btn)
        controls_layout.addWidget(save_btn)
        controls_layout.addWidget(load_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Drawing area
        self.canvas = QLabel()
        self.canvas.setMinimumSize(700, 500)
        self.canvas.setStyleSheet("border: 2px solid #333; background-color: white;")
        self.canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Initialize pixmap
        self.pixmap = QPixmap(700, 500)
        self.pixmap.fill(Qt.GlobalColor.white)
        self.canvas.setPixmap(self.pixmap)
        
        layout.addWidget(self.canvas)
        
        # Instructions
        instructions = QLabel("Instructions: Click and drag to draw. Use the controls above to change brush size and color.")
        instructions.setStyleSheet("color: #666; font-style: italic; padding: 10px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        self.setLayout(layout)
        
    def change_brush_size(self, value):
        """Change the brush size"""
        self.brush_size = value
        self.size_display.setText(str(value))
        
    def choose_color(self):
        """Open color dialog to choose brush color"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.set_color(color)
            
    def set_color(self, color):
        """Set the brush color"""
        self.brush_color = color
        self.color_btn.setStyleSheet(f"background-color: {color.name()}; color: white; font-weight: bold; padding: 8px;")
        
    def clear_canvas(self):
        """Clear the drawing canvas"""
        reply = QMessageBox.question(
            self, "Clear Canvas", 
            "Are you sure you want to clear the canvas?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.pixmap.fill(Qt.GlobalColor.white)
            self.canvas.setPixmap(self.pixmap)
            
    def save_image(self):
        """Save the drawing to a file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", "", 
            "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)"
        )
        if file_path:
            if self.pixmap.save(file_path):
                QMessageBox.information(self, "Success", f"Image saved to {file_path}")
            else:
                QMessageBox.warning(self, "Error", "Failed to save image")
                
    def load_image(self):
        """Load an image to draw on"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Image", "", 
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp);;All Files (*)"
        )
        if file_path:
            loaded_pixmap = QPixmap(file_path)
            if not loaded_pixmap.isNull():
                # Scale image to fit canvas
                self.pixmap = loaded_pixmap.scaled(700, 500, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                # Center on white background
                final_pixmap = QPixmap(700, 500)
                final_pixmap.fill(Qt.GlobalColor.white)
                painter = QPainter(final_pixmap)
                x = (700 - self.pixmap.width()) // 2
                y = (500 - self.pixmap.height()) // 2
                painter.drawPixmap(x, y, self.pixmap)
                painter.end()
                self.pixmap = final_pixmap
                self.canvas.setPixmap(self.pixmap)
            else:
                QMessageBox.warning(self, "Error", "Failed to load image")
        
    def mousePressEvent(self, event):
        """Handle mouse press events for drawing"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Convert global coordinates to canvas coordinates
            canvas_pos = self.canvas.mapFromGlobal(event.globalPosition().toPoint())
            if self.canvas.rect().contains(canvas_pos):
                self.drawing = True
                self.last_point = canvas_pos
                
    def mouseMoveEvent(self, event):
        """Handle mouse move events for drawing"""
        if event.buttons() & Qt.MouseButton.LeftButton and self.drawing:
            # Convert global coordinates to canvas coordinates
            canvas_pos = self.canvas.mapFromGlobal(event.globalPosition().toPoint())
            if self.canvas.rect().contains(canvas_pos):
                current_point = canvas_pos
                
                painter = QPainter(self.pixmap)
                painter.setPen(QPen(self.brush_color, self.brush_size, 
                                  Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                
                if not self.last_point.isNull():
                    painter.drawLine(self.last_point, current_point)
                    
                painter.end()
                self.last_point = current_point
                self.canvas.setPixmap(self.pixmap)
                
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = False
            self.last_point = QPoint()