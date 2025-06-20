"""
Todo Tab - Simple todo list with add, complete, and delete functionality
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLineEdit, QListWidget, QMessageBox)
from PySide6.QtCore import Qt


class TodoTab(QWidget):
    """Todo list tab with task management functionality"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Initialize the todo list interface"""
        layout = QVBoxLayout()
        
        # Title
        title_layout = QHBoxLayout()
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # Input section
        input_layout = QHBoxLayout()
        self.todo_input = QLineEdit()
        self.todo_input.setPlaceholderText("Enter a new task...")
        self.todo_input.returnPressed.connect(self.add_todo)
        
        add_btn = QPushButton("Add Task")
        add_btn.clicked.connect(self.add_todo)
        add_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        
        input_layout.addWidget(self.todo_input)
        input_layout.addWidget(add_btn)
        
        layout.addLayout(input_layout)
        
        # Todo list
        self.todo_list = QListWidget()
        self.todo_list.setStyleSheet("""
            QListWidget {
                font-size: 14px;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
            }
        """)
        layout.addWidget(self.todo_list)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        complete_btn = QPushButton("Toggle Complete")
        complete_btn.clicked.connect(self.mark_complete)
        complete_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 8px;")
        
        delete_btn = QPushButton("Delete Task")
        delete_btn.clicked.connect(self.delete_task)
        delete_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 8px;")
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_all)
        clear_btn.setStyleSheet("background-color: #ff9800; color: white; font-weight: bold; padding: 8px;")
        
        # Statistics button
        stats_btn = QPushButton("Show Statistics")
        stats_btn.clicked.connect(self.show_statistics)
        stats_btn.setStyleSheet("background-color: #9c27b0; color: white; font-weight: bold; padding: 8px;")
        
        button_layout.addWidget(complete_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addWidget(clear_btn)
        button_layout.addWidget(stats_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Add some sample tasks
        self.add_sample_tasks()
        
    def add_sample_tasks(self):
        """Add some sample tasks for demonstration"""
        sample_tasks = [
            "☐ Welcome to the Todo List!",
            "☐ Click 'Toggle Complete' to mark tasks as done",
            "☐ Add your own tasks using the input field above",
            "✓ This task is already completed"
        ]
        
        for task in sample_tasks:
            self.todo_list.addItem(task)
        
    def add_todo(self):
        """Add a new todo item"""
        text = self.todo_input.text().strip()
        if text:
            self.todo_list.addItem(f"☐ {text}")
            self.todo_input.clear()
            self.todo_input.setFocus()  # Keep focus on input field
        else:
            QMessageBox.information(self, "Empty Task", "Please enter a task description.")
            
    def mark_complete(self):
        """Toggle completion status of selected task"""
        current_item = self.todo_list.currentItem()
        if current_item:
            text = current_item.text()
            if text.startswith("☐"):
                # Mark as complete
                new_text = text.replace("☐", "✓")
                current_item.setText(new_text)
                current_item.setStyleSheet("color: #4CAF50; text-decoration: line-through;")
            elif text.startswith("✓"):
                # Mark as incomplete
                new_text = text.replace("✓", "☐")
                current_item.setText(new_text)
                current_item.setStyleSheet("color: black; text-decoration: none;")
        else:
            QMessageBox.information(self, "No Selection", "Please select a task to toggle.")
                
    def delete_task(self):
        """Delete the selected task"""
        current_row = self.todo_list.currentRow()
        if current_row >= 0:
            reply = QMessageBox.question(
                self, "Confirm Delete", 
                "Are you sure you want to delete this task?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.todo_list.takeItem(current_row)
        else:
            QMessageBox.information(self, "No Selection", "Please select a task to delete.")
            
    def clear_all(self):
        """Clear all tasks after confirmation"""
        if self.todo_list.count() == 0:
            QMessageBox.information(self, "No Tasks", "There are no tasks to clear.")
            return
            
        reply = QMessageBox.question(
            self, "Clear All", 
            "Are you sure you want to clear all tasks?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.todo_list.clear()
            
    def show_statistics(self):
        """Show task statistics"""
        total_tasks = self.todo_list.count()
        completed_tasks = 0
        incomplete_tasks = 0
        
        for i in range(total_tasks):
            item = self.todo_list.item(i)
            if item.text().startswith("✓"):
                completed_tasks += 1
            elif item.text().startswith("☐"):
                incomplete_tasks += 1
                
        if total_tasks > 0:
            completion_rate = (completed_tasks / total_tasks) * 100
        else:
            completion_rate = 0
            
        stats_text = f"""Task Statistics:
        
Total Tasks: {total_tasks}
Completed: {completed_tasks}
Incomplete: {incomplete_tasks}
Completion Rate: {completion_rate:.1f}%"""
        
        QMessageBox.information(self, "Task Statistics", stats_text)