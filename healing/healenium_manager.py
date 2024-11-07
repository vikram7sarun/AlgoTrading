import sys
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton,
                             QLabel, QComboBox, QTabWidget, QTextEdit, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from selenium import webdriver
from selenium.webdriver.common.by import By


class HealeniumDB:
    def __init__(self):
        self.conn = sqlite3.connect('healenium.db')
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        # Table for storing original locators
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                element_name TEXT,
                locator_type TEXT,
                locator_value TEXT,
                page_url TEXT,
                created_at TIMESTAMP
            )
        ''')

        # Table for storing healing results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS healing_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_locator_id INTEGER,
                healed_locator_type TEXT,
                healed_locator_value TEXT,
                similarity_score FLOAT,
                status TEXT,
                created_at TIMESTAMP,
                FOREIGN KEY (original_locator_id) REFERENCES locators (id)
            )
        ''')

        self.conn.commit()


class LocatorHealer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()

    def find_alternative_locators(self, original_locator, page_source):
        """Find alternative locators using ML-based similarity matching"""
        # Extract all potential elements from page source
        potential_elements = self._extract_elements(page_source)

        # Vectorize and compare similarity
        vectors = self.vectorizer.fit_transform([original_locator] + potential_elements)
        similarity_matrix = cosine_similarity(vectors[0:1], vectors[1:])

        # Get top matches
        alternatives = []
        for idx, score in enumerate(similarity_matrix[0]):
            if score > 0.7:  # Threshold for similarity
                alternatives.append({
                    'locator': potential_elements[idx],
                    'score': float(score)
                })

        return sorted(alternatives, key=lambda x: x['score'], reverse=True)

    def _extract_elements(self, page_source):
        """Extract potential elements from page source"""
        # This is a simplified version - in practice, you'd want more sophisticated parsing
        id_pattern = r'id="([^"]*)"'
        class_pattern = r'class="([^"]*)"'

        ids = re.findall(id_pattern, page_source)
        classes = re.findall(class_pattern, page_source)

        return ids + classes


class HealeniumGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = HealeniumDB()
        self.healer = LocatorHealer()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Healenium Test Management')
        self.setGeometry(100, 100, 1200, 800)

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()

        # Create tabs
        tabs = QTabWidget()
        tabs.addTab(self.create_dashboard_tab(), "Dashboard")
        tabs.addTab(self.create_locators_tab(), "Locators")
        tabs.addTab(self.create_healing_tab(), "Healing Results")

        layout.addWidget(tabs)
        main_widget.setLayout(layout)

        # Start periodic refresh
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds

    def create_dashboard_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Add statistics widgets
        stats_layout = QHBoxLayout()

        total_locators = QLabel("Total Locators: 0")
        healed_locators = QLabel("Healed Locators: 0")
        success_rate = QLabel("Success Rate: 0%")

        stats_layout.addWidget(total_locators)
        stats_layout.addWidget(healed_locators)
        stats_layout.addWidget(success_rate)

        layout.addLayout(stats_layout)

        # Add recent activity table
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(4)
        self.activity_table.setHorizontalHeaderLabels(["Timestamp", "Element", "Action", "Status"])
        layout.addWidget(self.activity_table)

        widget.setLayout(layout)
        return widget

    def create_locators_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Add controls
        controls_layout = QHBoxLayout()

        self.locator_type_combo = QComboBox()
        self.locator_type_combo.addItems(["CSS", "XPath", "ID", "Class Name"])

        add_button = QPushButton("Add Locator")
        add_button.clicked.connect(self.add_locator)

        controls_layout.addWidget(QLabel("Locator Type:"))
        controls_layout.addWidget(self.locator_type_combo)
        controls_layout.addWidget(add_button)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # Add locators table
        self.locators_table = QTableWidget()
        self.locators_table.setColumnCount(5)
        self.locators_table.setHorizontalHeaderLabels(
            ["Element Name", "Type", "Value", "Page URL", "Created At"])
        layout.addWidget(self.locators_table)

        widget.setLayout(layout)
        return widget

    def create_healing_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Add healing results table
        self.healing_table = QTableWidget()
        self.healing_table.setColumnCount(6)
        self.healing_table.setHorizontalHeaderLabels(
            ["Original Locator", "Healed Type", "Healed Value",
             "Similarity Score", "Status", "Created At"])
        layout.addWidget(self.healing_table)

        widget.setLayout(layout)
        return widget

    def add_locator(self):
        # Add new locator to database
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT INTO locators (element_name, locator_type, locator_value, page_url, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', ("New Element", self.locator_type_combo.currentText(), "", "", datetime.now()))
        self.db.conn.commit()
        self.refresh_data()

    def refresh_data(self):
        """Refresh all data displays"""
        # Update locators table
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT * FROM locators ORDER BY created_at DESC')
        locators = cursor.fetchall()

        self.locators_table.setRowCount(len(locators))
        for i, locator in enumerate(locators):
            for j, value in enumerate(locator[1:]):  # Skip id
                self.locators_table.setItem(i, j, QTableWidgetItem(str(value)))

        # Update healing results table
        cursor.execute('''
            SELECT l.element_name, h.healed_locator_type, h.healed_locator_value,
                   h.similarity_score, h.status, h.created_at
            FROM healing_results h
            JOIN locators l ON h.original_locator_id = l.id
            ORDER BY h.created_at DESC
        ''')
        results = cursor.fetchall()

        self.healing_table.setRowCount(len(results))
        for i, result in enumerate(results):
            for j, value in enumerate(result):
                self.healing_table.setItem(i, j, QTableWidgetItem(str(value)))


class HealeniumTestRunner:
    def __init__(self, db):
        self.db = db
        self.healer = LocatorHealer()

    def run_test(self, test_case):
        """Run a test case with self-healing capabilities"""
        driver = webdriver.Chrome()  # Or other WebDriver

        try:
            # Execute test steps
            for step in test_case.steps:
                try:
                    # Try original locator
                    element = driver.find_element(step.by, step.locator)
                except:
                    # If original fails, try to heal
                    page_source = driver.page_source
                    alternatives = self.healer.find_alternative_locators(step.locator, page_source)

                    if alternatives:
                        # Try alternative locators
                        for alt in alternatives:
                            try:
                                element = driver.find_element(By.CSS_SELECTOR, alt['locator'])

                                # Store healing result
                                cursor = self.db.conn.cursor()
                                cursor.execute('''
                                    INSERT INTO healing_results 
                                    (original_locator_id, healed_locator_type, healed_locator_value,
                                     similarity_score, status, created_at)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                ''', (step.locator_id, "CSS", alt['locator'],
                                      alt['score'], "SUCCESS", datetime.now()))
                                self.db.conn.commit()

                                break
                            except:
                                continue

                    if not element:
                        raise Exception(f"Could not heal locator: {step.locator}")

                # Execute step action
                step.execute(element)

        finally:
            driver.quit()


def main():
    app = QApplication(sys.argv)
    gui = HealeniumGUI()
    gui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()