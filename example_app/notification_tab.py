"""
Notification Tab - Desktop notification demonstration and testing
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QTextEdit, QLineEdit, QComboBox,
                               QGroupBox, QGridLayout, QMessageBox, QCheckBox,
                               QSpinBox, QSlider)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon


class NotificationTab(QWidget):
    """Desktop notification demonstration and testing tab"""
    
    def __init__(self):
        super().__init__()
        self.notification_count = 0
        self.init_ui()
        
    def init_ui(self):
        """Initialize the notification interface"""
        layout = QVBoxLayout()
        
        # Title and description
        title_label = QLabel("🔔 Desktop Notifications")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px; color: #2196F3;")
        layout.addWidget(title_label)
        
        description = QLabel("""
This tab demonstrates different types of notifications and message boxes available in PySide6.
You can customize notification content and test various notification styles.
        """.strip())
        description.setStyleSheet("color: #666; font-style: italic; margin: 10px; padding: 10px; background-color: #f0f8ff; border-radius: 5px;")
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Custom notification section
        custom_group = QGroupBox("Custom Notification")
        custom_layout = QGridLayout()
        
        custom_layout.addWidget(QLabel("Title:"), 0, 0)
        self.title_input = QLineEdit("Hello from PySide6!")
        self.title_input.setPlaceholderText("Enter notification title...")
        custom_layout.addWidget(self.title_input, 0, 1)
        
        custom_layout.addWidget(QLabel("Message:"), 1, 0)
        self.message_input = QTextEdit()
        self.message_input.setPlainText("This is a custom notification message from your PySide6 application!")
        self.message_input.setMaximumHeight(80)
        self.message_input.setPlaceholderText("Enter your notification message...")
        custom_layout.addWidget(self.message_input, 1, 1)
        
        custom_layout.addWidget(QLabel("Type:"), 2, 0)
        self.notification_type = QComboBox()
        self.notification_type.addItems(["Information", "Warning", "Critical", "Question"])
        custom_layout.addWidget(self.notification_type, 2, 1)
        
        # Notification options
        custom_layout.addWidget(QLabel("Options:"), 3, 0)
        options_layout = QHBoxLayout()
        
        self.detailed_text_check = QCheckBox("Include detailed text")
        self.sound_check = QCheckBox("Play sound")
        self.auto_close_check = QCheckBox("Auto close")
        
        options_layout.addWidget(self.detailed_text_check)
        options_layout.addWidget(self.sound_check)
        options_layout.addWidget(self.auto_close_check)
        options_layout.addStretch()
        
        options_widget = QWidget()
        options_widget.setLayout(options_layout)
        custom_layout.addWidget(options_widget, 3, 1)
        
        # Send button
        send_custom_btn = QPushButton("Send Custom Notification")
        send_custom_btn.clicked.connect(self.send_custom_notification)
        send_custom_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; font-size: 14px;")
        custom_layout.addWidget(send_custom_btn, 4, 0, 1, 2)
        
        custom_group.setLayout(custom_layout)
        layout.addWidget(custom_group)
        
        # Quick notification buttons
        quick_group = QGroupBox("Quick Notifications")
        quick_layout = QGridLayout()
        
        # Row 1
        info_btn = QPushButton("ℹ️ Information")
        info_btn.clicked.connect(lambda: self.send_example_notification("info"))
        info_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 10px;")
        
        warning_btn = QPushButton("⚠️ Warning")
        warning_btn.clicked.connect(lambda: self.send_example_notification("warning"))
        warning_btn.setStyleSheet("background-color: #ff9800; color: white; font-weight: bold; padding: 10px;")
        
        error_btn = QPushButton("❌ Error")
        error_btn.clicked.connect(lambda: self.send_example_notification("error"))
        error_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 10px;")
        
        question_btn = QPushButton("❓ Question")
        question_btn.clicked.connect(lambda: self.send_example_notification("question"))
        question_btn.setStyleSheet("background-color: #9c27b0; color: white; font-weight: bold; padding: 10px;")
        
        quick_layout.addWidget(info_btn, 0, 0)
        quick_layout.addWidget(warning_btn, 0, 1)
        quick_layout.addWidget(error_btn, 0, 2)
        quick_layout.addWidget(question_btn, 0, 3)
        
        # Row 2
        success_btn = QPushButton("✅ Success")
        success_btn.clicked.connect(lambda: self.send_example_notification("success"))
        success_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        
        progress_btn = QPushButton("⏳ Progress")
        progress_btn.clicked.connect(self.show_progress_notification)
        progress_btn.setStyleSheet("background-color: #607d8b; color: white; font-weight: bold; padding: 10px;")
        
        custom_icon_btn = QPushButton("🎨 Custom")
        custom_icon_btn.clicked.connect(self.show_custom_notification)
        custom_icon_btn.setStyleSheet("background-color: #795548; color: white; font-weight: bold; padding: 10px;")
        
        batch_btn = QPushButton("📦 Batch Test")
        batch_btn.clicked.connect(self.send_batch_notifications)
        batch_btn.setStyleSheet("background-color: #ff5722; color: white; font-weight: bold; padding: 10px;")
        
        quick_layout.addWidget(success_btn, 1, 0)
        quick_layout.addWidget(progress_btn, 1, 1)
        quick_layout.addWidget(custom_icon_btn, 1, 2)
        quick_layout.addWidget(batch_btn, 1, 3)
        
        quick_group.setLayout(quick_layout)
        layout.addWidget(quick_group)
        
        # Advanced features
        advanced_group = QGroupBox("Advanced Features")
        advanced_layout = QHBoxLayout()
        
        # Timed notifications
        timed_layout = QVBoxLayout()
        timed_layout.addWidget(QLabel("Timed Notifications:"))
        
        timer_layout = QHBoxLayout()
        timer_layout.addWidget(QLabel("Delay (seconds):"))
        self.timer_spin = QSpinBox()
        self.timer_spin.setRange(1, 60)
        self.timer_spin.setValue(5)
        timer_layout.addWidget(self.timer_spin)
        
        timed_btn = QPushButton("Schedule Notification")
        timed_btn.clicked.connect(self.schedule_notification)
        timer_layout.addWidget(timed_btn)
        
        timed_layout.addLayout(timer_layout)
        
        # Statistics
        stats_layout = QVBoxLayout()
        stats_layout.addWidget(QLabel("Statistics:"))
        
        self.count_label = QLabel("Notifications sent: 0")
        self.count_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        stats_layout.addWidget(self.count_label)
        
        reset_btn = QPushButton("Reset Counter")
        reset_btn.clicked.connect(self.reset_counter)
        stats_layout.addWidget(reset_btn)
        
        advanced_layout.addLayout(timed_layout)
        advanced_layout.addWidget(QLabel("|"))
        advanced_layout.addLayout(stats_layout)
        advanced_layout.addStretch()
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # System information
        info_group = QGroupBox("System Information")
        info_layout = QVBoxLayout()
        
        info_text = QLabel("""
Platform Notes:
• Windows: Notifications appear in the system tray area
• macOS: Notifications integrate with Notification Center
• Linux: Behavior depends on desktop environment
• Some systems may require notification permissions

Message Box Types:
• Information: General informational messages
• Warning: Important notices that require attention
• Critical: Error messages and critical alerts
• Question: Interactive dialogs requiring user response
        """.strip())
        info_text.setStyleSheet("color: #666; font-size: 11px; padding: 10px; background-color: #f9f9f9; border-radius: 5px;")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def send_custom_notification(self):
        """Send a custom notification with user input"""
        title = self.title_input.text().strip() or "Custom Notification"
        message = self.message_input.toPlainText().strip() or "This is a custom notification message."
        notification_type = self.notification_type.currentText()
        
        # Add detailed text if checked
        if self.detailed_text_check.isChecked():
            detailed_text = f"""
Notification Details:
• Type: {notification_type}
• Time: {QTimer().remainingTime() if hasattr(QTimer(), 'remainingTime') else 'Now'}
• Source: PySide6 Multi-Tab Application
• Custom message from user input
            """.strip()
            message += f"\n\n{detailed_text}"
        
        self.show_notification(title, message, notification_type)
        
    def send_example_notification(self, notification_type):
        """Send predefined example notifications"""
        examples = {
            "info": ("Information", "This is an informational message.\n\nIt provides helpful details about the current operation."),
            "warning": ("Warning", "This is a warning message.\n\nPlease pay attention to this important notice."),
            "error": ("Error", "This is an error message.\n\nSomething went wrong and requires your attention."),
            "question": ("Question", "This is a question dialog.\n\nWould you like to proceed with this action?"),
            "success": ("Success", "Operation completed successfully!\n\nAll tasks have been finished without errors.")
        }
        
        if notification_type in examples:
            title, message = examples[notification_type]
            msg_type = "Critical" if notification_type == "error" else notification_type.title()
            if notification_type == "success":
                msg_type = "Information"
            self.show_notification(title, message, msg_type)
            
    def show_notification(self, title, message, msg_type):
        """Display notification based on type"""
        self.notification_count += 1
        self.update_counter()
        
        if msg_type == "Information":
            QMessageBox.information(self, title, message)
        elif msg_type == "Warning":
            QMessageBox.warning(self, title, message)
        elif msg_type == "Critical":
            QMessageBox.critical(self, title, message)
        elif msg_type == "Question":
            reply = QMessageBox.question(self, title, message)
            response = "Yes" if reply == QMessageBox.StandardButton.Yes else "No"
            QMessageBox.information(self, "Response", f"You clicked: {response}")
            
    def show_progress_notification(self):
        """Show a progress-style notification"""
        self.show_notification(
            "Progress Update", 
            "Processing your request...\n\n⏳ Please wait while the operation completes.\n\nStep 3 of 5 finished successfully.",
            "Information"
        )
        
    def show_custom_notification(self):
        """Show a notification with custom styling"""
        self.show_notification(
            "🎨 Custom Styled Notification",
            "This notification demonstrates custom content:\n\n🌟 Feature: Advanced styling\n📊 Status: Active\n🔧 Mode: Demo\n\nCustom notifications can include emojis, formatting, and structured content.",
            "Information"
        )
        
    def send_batch_notifications(self):
        """Send multiple notifications for testing"""
        batch_messages = [
            ("Batch Test 1/3", "First notification in the batch test.", "Information"),
            ("Batch Test 2/3", "Second notification - Warning type.", "Warning"),
            ("Batch Test 3/3", "Final notification in the batch test.", "Information")
        ]
        
        for i, (title, message, msg_type) in enumerate(batch_messages):
            QTimer.singleShot(i * 1000, lambda t=title, m=message, mt=msg_type: self.show_notification(t, m, mt))
            
    def schedule_notification(self):
        """Schedule a notification for later"""
        delay = self.timer_spin.value() * 1000  # Convert to milliseconds
        
        QMessageBox.information(
            self, "Notification Scheduled", 
            f"A notification has been scheduled to appear in {self.timer_spin.value()} seconds."
        )
        
        QTimer.singleShot(
            delay, 
            lambda: self.show_notification(
                "⏰ Scheduled Notification",
                f"This notification was scheduled {self.timer_spin.value()} seconds ago.\n\nScheduled notifications are useful for reminders and delayed alerts.",
                "Information"
            )
        )
        
    def update_counter(self):
        """Update the notification counter"""
        self.count_label.setText(f"Notifications sent: {self.notification_count}")
        
    def reset_counter(self):
        """Reset the notification counter"""
        self.notification_count = 0
        self.update_counter()
        QMessageBox.information(self, "Counter Reset", "Notification counter has been reset to zero.")