import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QFormLayout, QLabel, QLineEdit,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox)
from PyQt5.QtCore import Qt


class DataEntryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Entry Application")
        self.setGeometry(100, 100, 800, 600)

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout()
        main_widget.setLayout(layout)

        # Entry Form Section
        form_widget = QWidget()
        form_layout = QVBoxLayout()
        form_widget.setLayout(form_layout)

        # Create form
        input_form = QFormLayout()
        self.name_input = QLineEdit()
        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.address_input = QLineEdit()

        input_form.addRow("Name:", self.name_input)
        input_form.addRow("Email:", self.email_input)
        input_form.addRow("Phone:", self.phone_input)
        input_form.addRow("Address:", self.address_input)

        # Buttons
        button_layout = QHBoxLayout()
        self.submit_button = QPushButton("Submit")
        self.clear_button = QPushButton("Clear")
        self.delete_button = QPushButton("Delete Selected")

        button_layout.addWidget(self.submit_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.delete_button)

        # Add form and buttons to form layout
        form_layout.addLayout(input_form)
        form_layout.addLayout(button_layout)
        form_layout.addStretch()

        # Table Section
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Email", "Phone", "Address"])
        header = self.table.horizontalHeader()
        for i in range(4):
            header.setSectionResizeMode(i, header.Stretch)

        # Add widgets to main layout
        layout.addWidget(form_widget, 1)
        layout.addWidget(self.table, 2)

        # Connect signals
        self.submit_button.clicked.connect(self.submit_data)
        self.clear_button.clicked.connect(self.clear_form)
        self.delete_button.clicked.connect(self.delete_selected)

    def submit_data(self):
        # Get data from form
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()
        address = self.address_input.text().strip()

        # Basic validation
        if not all([name, email, phone, address]):
            QMessageBox.warning(self, "Error", "All fields are required!")
            return

        # Add new row to table
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        # Add data to row
        self.table.setItem(row_position, 0, QTableWidgetItem(name))
        self.table.setItem(row_position, 1, QTableWidgetItem(email))
        self.table.setItem(row_position, 2, QTableWidgetItem(phone))
        self.table.setItem(row_position, 3, QTableWidgetItem(address))

        # Clear form after submission
        self.clear_form()

    def clear_form(self):
        self.name_input.clear()
        self.email_input.clear()
        self.phone_input.clear()
        self.address_input.clear()

    def delete_selected(self):
        selected_rows = set(item.row() for item in self.table.selectedItems())
        for row in sorted(selected_rows, reverse=True):
            self.table.removeRow(row)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DataEntryApp()
    window.show()
    sys.exit(app.exec_())