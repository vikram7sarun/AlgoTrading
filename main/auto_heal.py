import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTabWidget, QFormLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget, QTextEdit,
                             QTableWidgetItem, QMessageBox, QComboBox)
from PyQt5.QtCore import Qt


class HealeniumManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Healenium Test Management")
        self.setGeometry(100, 100, 1200, 800)

        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        # Initialize tabs
        self.init_test_cases_tab()
        self.init_locators_tab()
        self.init_healing_history_tab()

    def init_test_cases_tab(self):
        test_cases_widget = QWidget()
        layout = QHBoxLayout()

        # Form section
        form_widget = QWidget()
        form_layout = QVBoxLayout()

        # Create form
        input_form = QFormLayout()
        self.test_name = QLineEdit()
        self.test_description = QTextEdit()
        self.test_description.setMaximumHeight(100)
        self.locator_type = QComboBox()
        self.locator_type.addItems(["CSS", "XPath", "ID", "Class Name", "Name", "Tag Name"])
        self.locator_value = QLineEdit()
        self.test_status = QComboBox()
        self.test_status.addItems(["Active", "Inactive", "Maintenance"])

        input_form.addRow("Test Name:", self.test_name)
        input_form.addRow("Description:", self.test_description)
        input_form.addRow("Locator Type:", self.locator_type)
        input_form.addRow("Locator Value:", self.locator_value)
        input_form.addRow("Status:", self.test_status)

        # Buttons
        button_layout = QHBoxLayout()
        self.add_test_button = QPushButton("Add Test")
        self.update_test_button = QPushButton("Update")
        self.delete_test_button = QPushButton("Delete")

        button_layout.addWidget(self.add_test_button)
        button_layout.addWidget(self.update_test_button)
        button_layout.addWidget(self.delete_test_button)

        form_layout.addLayout(input_form)
        form_layout.addLayout(button_layout)
        form_layout.addStretch()
        form_widget.setLayout(form_layout)

        # Table section
        self.test_table = QTableWidget()
        self.test_table.setColumnCount(5)
        self.test_table.setHorizontalHeaderLabels([
            "Test Name", "Description", "Locator Type",
            "Locator Value", "Status"
        ])
        header = self.test_table.horizontalHeader()
        for i in range(5):
            header.setSectionResizeMode(i, header.Stretch)

        # Add widgets to layout
        layout.addWidget(form_widget, 1)
        layout.addWidget(self.test_table, 2)

        # Connect signals
        self.add_test_button.clicked.connect(self.add_test_case)
        self.update_test_button.clicked.connect(self.update_test_case)
        self.delete_test_button.clicked.connect(self.delete_test_case)
        self.test_table.itemClicked.connect(self.load_test_data)

        test_cases_widget.setLayout(layout)
        self.tab_widget.addTab(test_cases_widget, "Test Cases")

    def init_locators_tab(self):
        locators_widget = QWidget()
        layout = QVBoxLayout()

        # Healing rules section
        rules_group = QWidget()
        rules_layout = QFormLayout()

        self.score_threshold = QLineEdit("0.8")
        self.recovery_tries = QLineEdit("3")
        self.healing_enabled = QComboBox()
        self.healing_enabled.addItems(["Enabled", "Disabled"])

        rules_layout.addRow("Score Threshold:", self.score_threshold)
        rules_layout.addRow("Recovery Attempts:", self.recovery_tries)
        rules_layout.addRow("Healing Status:", self.healing_enabled)

        save_rules_button = QPushButton("Save Rules")
        rules_layout.addRow("", save_rules_button)
        rules_group.setLayout(rules_layout)

        # Locators history table
        self.locators_table = QTableWidget()
        self.locators_table.setColumnCount(5)
        self.locators_table.setHorizontalHeaderLabels([
            "Test Name", "Original Locator", "Healed Locator",
            "Healing Score", "Last Updated"
        ])
        header = self.locators_table.horizontalHeader()
        for i in range(5):
            header.setSectionResizeMode(i, header.Stretch)

        layout.addWidget(rules_group)
        layout.addWidget(self.locators_table)
        locators_widget.setLayout(layout)
        self.tab_widget.addTab(locators_widget, "Locators")

    def init_healing_history_tab(self):
        history_widget = QWidget()
        layout = QVBoxLayout()

        # Search section
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by test name...")
        search_button = QPushButton("Search")
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)

        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Test Name", "Original Locator", "Healed Locator",
            "Status", "Healing Time", "Success Rate"
        ])
        header = self.history_table.horizontalHeader()
        for i in range(6):
            header.setSectionResizeMode(i, header.Stretch)

        layout.addLayout(search_layout)
        layout.addWidget(self.history_table)
        history_widget.setLayout(layout)
        self.tab_widget.addTab(history_widget, "Healing History")

    def add_test_case(self):
        name = self.test_name.text().strip()
        description = self.test_description.toPlainText().strip()
        locator_t = self.locator_type.currentText()
        locator_v = self.locator_value.text().strip()
        status = self.test_status.currentText()

        if not all([name, description, locator_v]):
            QMessageBox.warning(self, "Error", "Please fill all required fields!")
            return

        row_position = self.test_table.rowCount()
        self.test_table.insertRow(row_position)

        self.test_table.setItem(row_position, 0, QTableWidgetItem(name))
        self.test_table.setItem(row_position, 1, QTableWidgetItem(description))
        self.test_table.setItem(row_position, 2, QTableWidgetItem(locator_t))
        self.test_table.setItem(row_position, 3, QTableWidgetItem(locator_v))
        self.test_table.setItem(row_position, 4, QTableWidgetItem(status))

        self.clear_form()

    def update_test_case(self):
        selected_items = self.test_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select a test case to update!")
            return

        row = selected_items[0].row()

        name = self.test_name.text().strip()
        description = self.test_description.toPlainText().strip()
        locator_t = self.locator_type.currentText()
        locator_v = self.locator_value.text().strip()
        status = self.test_status.currentText()

        if not all([name, description, locator_v]):
            QMessageBox.warning(self, "Error", "Please fill all required fields!")
            return

        self.test_table.setItem(row, 0, QTableWidgetItem(name))
        self.test_table.setItem(row, 1, QTableWidgetItem(description))
        self.test_table.setItem(row, 2, QTableWidgetItem(locator_t))
        self.test_table.setItem(row, 3, QTableWidgetItem(locator_v))
        self.test_table.setItem(row, 4, QTableWidgetItem(status))

    def delete_test_case(self):
        selected_items = self.test_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select a test case to delete!")
            return

        reply = QMessageBox.question(self, "Confirm Delete",
                                     "Are you sure you want to delete this test case?",
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.test_table.removeRow(selected_items[0].row())
            self.clear_form()

    def load_test_data(self, item):
        row = item.row()
        self.test_name.setText(self.test_table.item(row, 0).text())
        self.test_description.setText(self.test_table.item(row, 1).text())
        self.locator_type.setCurrentText(self.test_table.item(row, 2).text())
        self.locator_value.setText(self.test_table.item(row, 3).text())
        self.test_status.setCurrentText(self.test_table.item(row, 4).text())

    def clear_form(self):
        self.test_name.clear()
        self.test_description.clear()
        self.locator_value.clear()
        self.locator_type.setCurrentIndex(0)
        self.test_status.setCurrentIndex(0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = HealeniumManager()
    window.show()
    sys.exit(app.exec_())