import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import sqlite3
from datetime import datetime
from pathlib import Path
import logging
import os


class HealeniumTestCase:
    def __init__(self, driver, db_conn):
        self.driver = driver
        self.db_conn = db_conn
        self.current_test_name = None

    def find_element(self, by, locator, element_name=None):
        """Find element with self-healing capability"""
        try:
            element = self.driver.find_element(by, locator)
            self._record_locator_success(by, locator, element_name)
            return element
        except Exception as e:
            logging.debug(f"Original locator failed: {by}={locator}")
            healed_element = self._heal_locator(by, locator, element_name)
            if healed_element:
                return healed_element
            raise e

    def _record_locator_success(self, by, locator, element_name):
        """Record successful locator usage"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO locators (
                    element_name,
                    locator_type,
                    locator_value,
                    page_url
                ) VALUES (?, ?, ?, ?)
            ''', (
                element_name or self.current_test_name,
                str(by),
                str(locator),
                self.driver.current_url
            ))
            self.db_conn.commit()
        except Exception as e:
            logging.error(f"Error recording locator success: {str(e)}")

    def _heal_locator(self, by, locator, element_name):
        """Attempt to heal broken locator"""
        try:
            # Record original failed locator
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO locators (
                    element_name,
                    locator_type,
                    locator_value,
                    page_url
                ) VALUES (?, ?, ?, ?)
            ''', (
                element_name or self.current_test_name,
                str(by),
                str(locator),
                self.driver.current_url
            ))
            original_locator_id = cursor.lastrowid
            self.db_conn.commit()

            alternative_strategies = [
                (By.ID, locator),
                (By.NAME, locator),
                (By.CLASS_NAME, locator),
                (By.CSS_SELECTOR, f"#{locator}"),
                (By.CSS_SELECTOR, f".{locator}"),
                (By.XPATH, f"//*[@id='{locator}']"),
                (By.XPATH, f"//*[@name='{locator}']"),
                (By.XPATH, f"//*[contains(@class, '{locator}')]")
            ]

            for alt_by, alt_locator in alternative_strategies:
                try:
                    element = self.driver.find_element(alt_by, alt_locator)

                    # Record successful healing
                    cursor.execute('''
                        INSERT INTO healing_results (
                            original_locator_id,
                            healed_locator_type,
                            healed_locator_value,
                            similarity_score,
                            status
                        ) VALUES (?, ?, ?, ?, ?)
                    ''', (
                        original_locator_id,
                        str(alt_by),
                        str(alt_locator),
                        0.8,
                        "SUCCESS"
                    ))
                    self.db_conn.commit()
                    return element
                except:
                    continue

            # Record failed healing attempt
            cursor.execute('''
                INSERT INTO healing_results (
                    original_locator_id,
                    healed_locator_type,
                    healed_locator_value,
                    similarity_score,
                    status
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                original_locator_id,
                str(by),
                str(locator),
                0.0,
                "FAILED"
            ))
            self.db_conn.commit()
            return None

        except Exception as e:
            logging.error(f"Error in healing process: {str(e)}")
            return None

@pytest.fixture(scope="session")
def db_connection():
    """Create and maintain database connection"""
    db_path = Path('healenium.db')
    conn = sqlite3.connect(str(db_path))
    yield conn
    conn.close()


@pytest.fixture
def healenium(request, db_connection):
    """Setup WebDriver with Healenium capabilities"""
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_argument("--headless=new")  # Uncomment for headless mode

    try:
        # Initialize WebDriver
        driver = webdriver.Chrome(options=chrome_options)
        driver.maximize_window()

        # Create Healenium test case
        healenium_test = HealeniumTestCase(driver, db_connection)
        healenium_test.current_test_name = request.node.name

        yield healenium_test

    except Exception as e:
        logging.error(f"Error setting up WebDriver: {str(e)}")
        raise
    finally:
        try:
            driver.quit()
        except Exception as e:
            logging.error(f"Error closing driver: {str(e)}")