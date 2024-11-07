import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QLabel, QTabWidget, QMessageBox,
                             QDialog, QGraphicsView, QGraphicsScene)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
import sqlite3
from datetime import datetime
from pathlib import Path
import subprocess
import threading
import logging


class ImageDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Test Failure Screenshot")
        self.setGeometry(100, 100, 800, 600)
        layout = QVBoxLayout()
        view = QGraphicsView()
        scene = QGraphicsScene()
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(780, 580, Qt.KeepAspectRatio)
            scene.addPixmap(scaled_pixmap)
            view.setScene(scene)
        layout.addWidget(view)
        self.setLayout(layout)


class HealeniumGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_logging()
        self.init_db()
        self.init_ui()

    def init_logging(self):
        os.makedirs("logs", exist_ok=True)
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/healenium_debug.log'),
                logging.StreamHandler()
            ]
        )

    def init_db(self):
        try:
            # First, delete existing database
            db_path = Path('healenium.db')
            if db_path.exists():
                db_path.unlink()

            self.conn = sqlite3.connect(str(db_path))
            cursor = self.conn.cursor()

            # Create locators table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS locators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    element_name TEXT NOT NULL,
                    locator_type TEXT NOT NULL,
                    locator_value TEXT NOT NULL,
                    page_url TEXT,
                    screenshot_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create healing results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS healing_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_locator_id INTEGER NOT NULL,
                    healed_locator_type TEXT NOT NULL,
                    healed_locator_value TEXT NOT NULL,
                    similarity_score FLOAT,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (original_locator_id) REFERENCES locators (id)
                )
            ''')

            self.conn.commit()
            logging.info("Database initialized successfully")
        except Exception as e:
            logging.error(f"Database initialization error: {str(e)}")
            raise

    def refresh_data(self):
        try:
            cursor = self.conn.cursor()

            # Update stats
            cursor.execute('SELECT COUNT(*) FROM locators')
            total_locators = cursor.fetchone()[0]
            self.total_locators_label.setText(f"Total Locators: {total_locators}")

            cursor.execute("SELECT COUNT(*) FROM healing_results WHERE status='SUCCESS'")
            healed_locators = cursor.fetchone()[0]
            self.healed_locators_label.setText(f"Healed Locators: {healed_locators}")

            if total_locators > 0:
                success_rate = (healed_locators / total_locators) * 100
                self.success_rate_label.setText(f"Success Rate: {success_rate:.1f}%")

            # Update locators table
            cursor.execute('''
                SELECT 
                    element_name,
                    locator_type,
                    locator_value,
                    page_url,
                    created_at
                FROM locators 
                ORDER BY created_at DESC
            ''')
            locators = cursor.fetchall()

            self.locators_table.setRowCount(len(locators))
            for i, row in enumerate(locators):
                for j, value in enumerate(row):
                    self.locators_table.setItem(i, j, QTableWidgetItem(str(value)))

            # Update dashboard (activity) table
            cursor.execute('''
                SELECT 
                    l.created_at,
                    l.element_name,
                    l.locator_value,
                    h.healed_locator_value,
                    h.status
                FROM locators l
                LEFT JOIN healing_results h ON l.id = h.original_locator_id
                ORDER BY l.created_at DESC
                LIMIT 10
            ''')
            activities = cursor.fetchall()

            self.activity_table.setRowCount(len(activities))
            for i, row in enumerate(activities):
                for j, value in enumerate(row):
                    if value is not None:
                        self.activity_table.setItem(i, j, QTableWidgetItem(str(value)))
                    else:
                        self.activity_table.setItem(i, j, QTableWidgetItem("N/A"))

            # Update healing results table
            cursor.execute('''
                SELECT 
                    l.locator_value,
                    h.healed_locator_type,
                    h.healed_locator_value,
                    h.similarity_score,
                    h.status,
                    h.created_at
                FROM healing_results h
                JOIN locators l ON h.original_locator_id = l.id
                ORDER BY h.created_at DESC
            ''')
            healing_results = cursor.fetchall()

            self.healing_table.setRowCount(len(healing_results))
            for i, row in enumerate(healing_results):
                for j, value in enumerate(row):
                    self.healing_table.setItem(i, j, QTableWidgetItem(str(value)))

        except Exception as e:
            logging.error(f"Error refreshing data: {str(e)}")

    # Also update the test case to properly save screenshots:
    def _record_screenshot(self, screenshot_path, locator_id):
        """Record screenshot path in database"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                UPDATE locators 
                SET screenshot_path = ? 
                WHERE id = ?
            ''', (screenshot_path, locator_id))
            self.db_conn.commit()
        except Exception as e:
            logging.error(f"Error recording screenshot: {str(e)}")

    def init_ui(self):
        self.setWindowTitle('Healenium Test Management')
        self.setGeometry(100, 100, 1200, 800)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()

        buttons_layout = QHBoxLayout()

        run_button = QPushButton('Run Tests')
        run_button.clicked.connect(self.run_tests)
        buttons_layout.addWidget(run_button)

        debug_button = QPushButton('Debug Tests')
        debug_button.clicked.connect(self.run_debug_tests)
        buttons_layout.addWidget(debug_button)

        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("font-weight: bold;")
        buttons_layout.addWidget(self.status_label)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        tabs = QTabWidget()
        tabs.addTab(self.create_dashboard_tab(), "Dashboard")
        tabs.addTab(self.create_locators_tab(), "Locators")
        tabs.addTab(self.create_healing_tab(), "Healing Results")

        layout.addWidget(tabs)
        main_widget.setLayout(layout)

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(1000)

    def create_dashboard_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        stats_layout = QHBoxLayout()
        self.total_locators_label = QLabel("Total Locators: 0")
        self.healed_locators_label = QLabel("Healed Locators: 0")
        self.success_rate_label = QLabel("Success Rate: 0%")

        stats_layout.addWidget(self.total_locators_label)
        stats_layout.addWidget(self.healed_locators_label)
        stats_layout.addWidget(self.success_rate_label)
        layout.addLayout(stats_layout)

        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(6)
        self.activity_table.setHorizontalHeaderLabels([
            "Timestamp", "Element", "Original Locator",
            "Healed Locator", "Status", "Screenshot"
        ])

        self.activity_table.setColumnWidth(5, 100)
        self.activity_table.cellClicked.connect(self.handle_cell_click)

        layout.addWidget(self.activity_table)
        widget.setLayout(layout)
        return widget

    def create_locators_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.locators_table = QTableWidget()
        self.locators_table.setColumnCount(6)
        self.locators_table.setHorizontalHeaderLabels([
            "Element Name", "Locator Type", "Locator Value",
            "Page URL", "Created At", "Screenshot"
        ])

        self.locators_table.setColumnWidth(5, 100)
        self.locators_table.cellClicked.connect(self.handle_cell_click)

        layout.addWidget(self.locators_table)
        widget.setLayout(layout)
        return widget

    def create_healing_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.healing_table = QTableWidget()
        self.healing_table.setColumnCount(6)
        self.healing_table.setHorizontalHeaderLabels([
            "Original Locator", "Healed Type", "Healed Value",
            "Similarity Score", "Status", "Created At"
        ])

        layout.addWidget(self.healing_table)
        widget.setLayout(layout)
        return widget

    def handle_cell_click(self, row, col):
        if col == 5:  # Screenshot column
            table = self.sender()
            item = table.item(row, col)
            if item:
                screenshot_path = item.data(Qt.UserRole)
                if screenshot_path and os.path.exists(screenshot_path):
                    dialog = ImageDialog(screenshot_path, self)
                    dialog.exec_()


    def run_tests(self):
        self.status_label.setText("Status: Running Tests...")
        self.status_label.setStyleSheet("color: blue; font-weight: bold;")

        def run_pytest():
            try:
                result = subprocess.run(
                    ['pytest', 'test_cases.py', '-v'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    self.update_status("Status: Tests Completed Successfully", "green")
                else:
                    self.update_status("Status: Tests Failed", "red")
            except Exception as e:
                self.update_status(f"Status: Error - {str(e)}", "red")

        thread = threading.Thread(target=run_pytest)
        thread.daemon = True
        thread.start()

    def run_debug_tests(self):
        self.status_label.setText("Status: Running Debug Tests...")
        self.status_label.setStyleSheet("color: blue; font-weight: bold;")

        def run_pytest_debug():
            try:
                os.makedirs("screenshots", exist_ok=True)

                result = subprocess.run(
                    ['python', '-m', 'pdb', '-m', 'pytest',
                     'test_cases.py', '-v', '--log-cli-level=DEBUG'],
                    capture_output=True,
                    text=True
                )

                logging.debug("Test Output:\n" + result.stdout)
                if result.stderr:
                    logging.error("Test Errors:\n" + result.stderr)

                if result.returncode == 0:
                    self.update_status("Status: Debug Tests Completed Successfully", "green")
                    self.show_debug_results(result.stdout)
                else:
                    self.update_status("Status: Debug Tests Failed", "red")
                    self.show_debug_results(result.stdout + "\n" + result.stderr)
            except Exception as e:
                self.update_status(f"Status: Error - {str(e)}", "red")
                logging.error(f"Debug test error: {str(e)}")

        thread = threading.Thread(target=run_pytest_debug)
        thread.daemon = True
        thread.start()

    def update_status(self, text, color):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def show_debug_results(self, output):
        msg = QMessageBox()
        msg.setWindowTitle("Debug Test Results")
        msg.setText("Test execution completed. Check the detailed output below:")
        msg.setDetailedText(output)
        msg.exec_()


def main():
    app = QApplication(sys.argv)
    gui = HealeniumGUI()
    gui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()