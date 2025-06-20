"""
Calculator Tab - Simple calculator with basic arithmetic operations
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                               QPushButton, QLineEdit, QMessageBox)
from PySide6.QtCore import Qt


class CalculatorTab(QWidget):
    """Simple calculator tab with basic arithmetic operations"""
    
    def __init__(self):
        super().__init__()
        self.current_input = ""
        self.result = 0
        self.operator = ""
        self.waiting_for_operand = False
        self.init_ui()
        
    def init_ui(self):
        """Initialize the calculator interface"""
        layout = QVBoxLayout()
        
        # Display
        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setStyleSheet("font-size: 18px; padding: 10px;")
        self.display.setText("0")
        layout.addWidget(self.display)
        
        # Buttons
        buttons_layout = QGridLayout()
        
        # Button definitions: (text, row, col, row_span, col_span)
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
            
            # Style operator buttons differently
            if text in ['+', '-', '×', '÷', '=']:
                btn.setStyleSheet("background-color: #ff9500; color: white; font-weight: bold;")
            elif text in ['C', '±', '%']:
                btn.setStyleSheet("background-color: #a6a6a6; color: black; font-weight: bold;")
            else:
                btn.setStyleSheet("background-color: #333333; color: white; font-weight: bold;")
                
            buttons_layout.addWidget(btn, row, col, row_span, col_span)
        
        buttons_widget = QWidget()
        buttons_widget.setLayout(buttons_layout)
        layout.addWidget(buttons_widget)
        
        self.setLayout(layout)
        
    def button_clicked(self, text):
        """Handle button click events"""
        if text.isdigit() or text == '.':
            self.handle_digit_or_decimal(text)
        elif text in ['+', '-', '×', '÷']:
            self.handle_operator(text)
        elif text == '=':
            self.calculate()
        elif text == 'C':
            self.clear()
        elif text == '±':
            self.toggle_sign()
        elif text == '%':
            self.handle_percentage()
            
    def handle_digit_or_decimal(self, text):
        """Handle digit and decimal point input"""
        if self.waiting_for_operand:
            self.current_input = text
            self.waiting_for_operand = False
        else:
            if text == '.' and '.' in self.current_input:
                return  # Don't allow multiple decimal points
            self.current_input += text
        self.display.setText(self.current_input)
        
    def handle_operator(self, text):
        """Handle arithmetic operator input"""
        if self.current_input:
            if self.operator and not self.waiting_for_operand:
                self.calculate()
            try:
                self.result = float(self.current_input)
                self.operator = text
                self.waiting_for_operand = True
            except ValueError:
                QMessageBox.warning(self, "Error", "Invalid number format!")
                self.clear()
                
    def calculate(self):
        """Perform the calculation"""
        if self.operator and self.current_input:
            try:
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
                        
                # Format result to remove unnecessary decimal places
                if self.result == int(self.result):
                    self.current_input = str(int(self.result))
                else:
                    self.current_input = f"{self.result:.10g}"
                    
                self.display.setText(self.current_input)
                self.operator = ""
                self.waiting_for_operand = True
                
            except ValueError:
                QMessageBox.warning(self, "Error", "Invalid calculation!")
                self.clear()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Calculation error: {str(e)}")
                self.clear()
                
    def clear(self):
        """Clear all values and reset calculator"""
        self.current_input = ""
        self.result = 0
        self.operator = ""
        self.waiting_for_operand = False
        self.display.setText("0")
        
    def toggle_sign(self):
        """Toggle the sign of the current number"""
        if self.current_input and self.current_input != "0":
            if self.current_input.startswith('-'):
                self.current_input = self.current_input[1:]
            else:
                self.current_input = '-' + self.current_input
            self.display.setText(self.current_input)
            
    def handle_percentage(self):
        """Convert current number to percentage"""
        if self.current_input:
            try:
                value = float(self.current_input) / 100
                if value == int(value):
                    self.current_input = str(int(value))
                else:
                    self.current_input = f"{value:.10g}"
                self.display.setText(self.current_input)
            except ValueError:
                QMessageBox.warning(self, "Error", "Invalid number for percentage!")