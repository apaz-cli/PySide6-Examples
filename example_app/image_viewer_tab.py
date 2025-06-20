"""
Image Viewer Tab - Drag and drop image viewer with zoom controls
"""

import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QScrollArea, QFileDialog, QMessageBox,
                               QSlider, QSpinBox, QGroupBox, QComboBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QDragEnterEvent, QDropEvent, QTransform


class ImageViewerTab(QWidget):
    """Image viewer with drag and drop, zoom, and rotation features"""
    
    def __init__(self):
        super().__init__()
        self.current_image = None
        self.original_pixmap = None
        self.scale_factor = 1.0
        self.rotation_angle = 0
        self.init_ui()
        
    def init_ui(self):
        """Initialize the image viewer interface"""
        layout = QVBoxLayout()
        
        # Controls section
        controls_group = QGroupBox("Image Controls")
        controls_layout = QHBoxLayout()
        
        # File operations
        open_btn = QPushButton("Open Image")
        open_btn.clicked.connect(self.open_image)
        open_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 8px;")
        
        save_btn = QPushButton("Save As")
        save_btn.clicked.connect(self.save_image)
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_image)
        clear_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 8px;")
        
        controls_layout.addWidget(open_btn)
        controls_layout.addWidget(save_btn)
        controls_layout.addWidget(clear_btn)
        controls_layout.addWidget(QLabel("|"))
        
        # Zoom controls
        zoom_in_btn = QPushButton("Zoom In (+)")
        zoom_in_btn.clicked.connect(self.zoom_in)
        
        zoom_out_btn = QPushButton("Zoom Out (-)")
        zoom_out_btn.clicked.connect(self.zoom_out)
        
        fit_btn = QPushButton("Fit to Window")
        fit_btn.clicked.connect(self.fit_to_window)
        
        actual_size_btn = QPushButton("Actual Size")
        actual_size_btn.clicked.connect(self.actual_size)
        
        controls_layout.addWidget(zoom_in_btn)
        controls_layout.addWidget(zoom_out_btn)
        controls_layout.addWidget(fit_btn)
        controls_layout.addWidget(actual_size_btn)
        controls_layout.addWidget(QLabel("|"))
        
        # Rotation controls
        rotate_left_btn = QPushButton("↺ Left")
        rotate_left_btn.clicked.connect(self.rotate_left)
        
        rotate_right_btn = QPushButton("↻ Right")
        rotate_right_btn.clicked.connect(self.rotate_right)
        
        controls_layout.addWidget(rotate_left_btn)
        controls_layout.addWidget(rotate_right_btn)
        controls_layout.addStretch()
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Zoom and info section
        info_layout = QHBoxLayout()
        
        # Zoom slider
        info_layout.addWidget(QLabel("Zoom:"))
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10, 500)  # 10% to 500%
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.slider_zoom_changed)
        info_layout.addWidget(self.zoom_slider)
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(50)
        info_layout.addWidget(self.zoom_label)
        
        info_layout.addWidget(QLabel("|"))
        
        # Image info
        self.image_info_label = QLabel("No image loaded")
        info_layout.addWidget(self.image_info_label)
        info_layout.addStretch()
        
        layout.addLayout(info_layout)
        
        # Image display area
        self.scroll_area = QScrollArea()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                background-color: #f9f9f9;
                color: #666;
                font-size: 16px;
                min-height: 400px;
            }
        """)
        self.image_label.setText("🖼️\n\nDrag and drop an image here\nor click 'Open Image' to browse\n\nSupported formats: PNG, JPG, JPEG, GIF, BMP, TIFF")
        
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: 1px solid #ddd; }")
        
        layout.addWidget(self.scroll_area)
        
        # Status bar
        self.status_label = QLabel("Ready - Drop an image or use 'Open Image'")
        self.status_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                file_path = urls[0].toLocalFile()
                if self.is_image_file(file_path):
                    event.acceptProposedAction()
                    self.image_label.setStyleSheet("""
                        QLabel {
                            border: 2px dashed #4CAF50;
                            background-color: #e8f5e8;
                            color: #2e7d32;
                            font-size: 16px;
                            min-height: 400px;
                        }
                    """)
                    
    def dragLeaveEvent(self, event):
        """Handle drag leave events"""
        if not self.current_image:
            self.image_label.setStyleSheet("""
                QLabel {
                    border: 2px dashed #aaa;
                    background-color: #f9f9f9;
                    color: #666;
                    font-size: 16px;
                    min-height: 400px;
                }
            """)
                    
    def dropEvent(self, event: QDropEvent):
        """Handle drop events"""
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            file_path = urls[0].toLocalFile()
            if self.is_image_file(file_path):
                self.load_image(file_path)
                
    def is_image_file(self, file_path):
        """Check if file is a supported image format"""
        return file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.svg'))
            
    def open_image(self):
        """Open image file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", 
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp *.tiff *.svg);;All Files (*)"
        )
        if file_path:
            self.load_image(file_path)
            
    def load_image(self, file_path):
        """Load image from file path"""
        try:
            self.original_pixmap = QPixmap(file_path)
            if self.original_pixmap.isNull():
                QMessageBox.warning(self, "Error", "Could not load image file. The file may be corrupted or in an unsupported format.")
                return
                
            self.current_image = file_path
            self.scale_factor = 1.0
            self.rotation_angle = 0
            
            # Update image display
            self.update_image_display()
            
            # Update info
            file_size = os.path.getsize(file_path)
            file_size_str = self.format_file_size(file_size)
            
            self.image_info_label.setText(
                f"{os.path.basename(file_path)} | "
                f"{self.original_pixmap.width()}×{self.original_pixmap.height()} | "
                f"{file_size_str}"
            )
            self.status_label.setText(f"Loaded: {os.path.basename(file_path)}")
            
            # Reset zoom slider
            self.zoom_slider.setValue(100)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load image: {str(e)}")
            
    def format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
            
    def update_image_display(self):
        """Update the image display with current transformations"""
        if not self.original_pixmap:
            return
            
        # Apply rotation
        transform = QTransform()
        transform.rotate(self.rotation_angle)
        rotated_pixmap = self.original_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        
        # Apply scaling
        if self.scale_factor != 1.0:
            new_size = rotated_pixmap.size() * self.scale_factor
            scaled_pixmap = rotated_pixmap.scaled(new_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        else:
            scaled_pixmap = rotated_pixmap
            
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.resize(scaled_pixmap.size())
        
        # Update zoom label
        zoom_percent = int(self.scale_factor * 100)
        self.zoom_label.setText(f"{zoom_percent}%")
        
        # Update image label style for loaded image
        self.image_label.setStyleSheet("""
            QLabel {
                border: none;
                background-color: white;
            }
        """)
            
    def zoom_in(self):
        """Zoom in by 25%"""
        if self.original_pixmap:
            self.scale_factor *= 1.25
            self.update_image_display()
            self.zoom_slider.setValue(int(self.scale_factor * 100))
            
    def zoom_out(self):
        """Zoom out by 25%"""
        if self.original_pixmap:
            self.scale_factor /= 1.25
            self.update_image_display()
            self.zoom_slider.setValue(int(self.scale_factor * 100))
            
    def fit_to_window(self):
        """Fit image to window size"""
        if not self.original_pixmap:
            return
            
        # Get available space
        available_size = self.scroll_area.size()
        
        # Account for rotation
        transform = QTransform()
        transform.rotate(self.rotation_angle)
        rotated_pixmap = self.original_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        image_size = rotated_pixmap.size()
        
        # Calculate scale factor to fit
        scale_x = (available_size.width() - 20) / image_size.width()  # 20px margin
        scale_y = (available_size.height() - 20) / image_size.height()
        self.scale_factor = min(scale_x, scale_y)
        
        self.update_image_display()
        self.zoom_slider.setValue(int(self.scale_factor * 100))
        
    def actual_size(self):
        """Show image at actual size (100%)"""
        if self.original_pixmap:
            self.scale_factor = 1.0
            self.update_image_display()
            self.zoom_slider.setValue(100)
            
    def rotate_left(self):
        """Rotate image 90 degrees counter-clockwise"""
        if self.original_pixmap:
            self.rotation_angle = (self.rotation_angle - 90) % 360
            self.update_image_display()
            
    def rotate_right(self):
        """Rotate image 90 degrees clockwise"""
        if self.original_pixmap:
            self.rotation_angle = (self.rotation_angle + 90) % 360
            self.update_image_display()
            
    def slider_zoom_changed(self, value):
        """Handle zoom slider changes"""
        if self.original_pixmap:
            self.scale_factor = value / 100.0
            self.update_image_display()
            
    def save_image(self):
        """Save current image with transformations"""
        if not self.original_pixmap:
            QMessageBox.information(self, "No Image", "No image to save.")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", "", 
            "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)"
        )
        if file_path:
            try:
                # Get current transformed pixmap
                current_pixmap = self.image_label.pixmap()
                if current_pixmap and current_pixmap.save(file_path):
                    QMessageBox.information(self, "Success", f"Image saved to {file_path}")
                else:
                    QMessageBox.warning(self, "Error", "Failed to save image")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not save image: {str(e)}")
                
    def clear_image(self):
        """Clear the current image"""
        if not self.current_image:
            QMessageBox.information(self, "No Image", "No image to clear.")
            return
            
        reply = QMessageBox.question(
            self, "Clear Image", 
            "Are you sure you want to clear the current image?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.current_image = None
            self.original_pixmap = None
            self.scale_factor = 1.0
            self.rotation_angle = 0
            
            self.image_label.clear()
            self.image_label.setText("🖼️\n\nDrag and drop an image here\nor click 'Open Image' to browse\n\nSupported formats: PNG, JPG, JPEG, GIF, BMP, TIFF")
            self.image_label.setStyleSheet("""
                QLabel {
                    border: 2px dashed #aaa;
                    background-color: #f9f9f9;
                    color: #666;
                    font-size: 16px;
                    min-height: 400px;
                }
            """)
            
            self.image_info_label.setText("No image loaded")
            self.status_label.setText("Ready - Drop an image or use 'Open Image'")
            self.zoom_slider.setValue(100)
            self.zoom_label.setText("100%")