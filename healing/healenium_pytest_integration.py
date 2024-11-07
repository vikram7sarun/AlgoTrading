import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sqlite3
from datetime import datetime
import os
from pathlib import Path


# Custom pytest plugin for Healenium integration
def pytest_configure(config):
    """Initialize Healenium database connection for the test session"""
    db_path = Path(__file__).parent / 'healenium.db'
    config.healenium_db = sqlite3.connect(str(db_path))
    config.healenium_results = []


def pytest_unconfigure(config):
    """Close database connection after test session"""
    if hasattr(config, 'healenium_db'):
        config.healenium_db.close()


class HealeniumTestCase:
    def __init__(self, driver, db_conn):
        self.driver = driver
        self.db_conn = db_conn
        self.current_test_name = None

    def find_element(self, by, locator, element_name=None):
        """Enhanced find_element with self-healing capabilities"""
        try:
            element = self.driver.find_element(by, locator)
            self._record_locator_success(by, locator, element_name)
            return element
        except Exception as e:
            healed_element = self._heal_locator(by, locator, element_name)
            if healed_element:
                return healed_element
            raise e

    def _record_locator_success(self, by, locator, element_name):
        """Record successful locator usage"""
        cursor = self.db_conn.cursor()
        cursor.execute('''
            INSERT INTO locators (element_name, locator_type, locator_value, page_url, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (element_name or self.current_test_name, by, locator,
              self.driver.current_url, datetime.now()))
        self.db_conn.commit()

    def _heal_locator(self, by, locator, element_name):
        """Attempt to heal a broken locator"""
        # Store the broken locator
        cursor = self.db_conn.cursor()
        cursor.execute('''
            INSERT INTO locators (element_name, locator_type, locator_value, page_url, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (element_name or self.current_test_name, by, locator,
              self.driver.current_url, datetime.now()))
        original_locator_id = cursor.lastrowid
        self.db_conn.commit()

        # Try alternative locator strategies
        alternative_strategies = [
            (By.ID, f"[id*='{locator}']"),
            (By.CLASS_NAME, f"[class*='{locator}']"),
            (By.CSS_SELECTOR, f"[data-testid*='{locator}']"),
            (By.XPATH, f"//*[contains(text(), '{locator}')]")
        ]

        for alt_by, alt_locator in alternative_strategies:
            try:
                element = self.driver.find_element(alt_by, alt_locator)
                # Record successful healing
                cursor.execute('''
                    INSERT INTO healing_results 
                    (original_locator_id, healed_locator_type, healed_locator_value,
                     similarity_score, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (original_locator_id, alt_by, alt_locator, 0.8, "SUCCESS", datetime.now()))
                self.db_conn.commit()
                return element
            except:
                continue

        # Record failed healing attempt
        cursor.execute('''
            INSERT INTO healing_results 
            (original_locator_id, healed_locator_type, healed_locator_value,
             similarity_score, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (original_locator_id, by, locator, 0.0, "FAILED", datetime.now()))
        self.db_conn.commit()
        return None


@pytest.fixture
def healenium(request):
    """Fixture to provide Healenium-enhanced WebDriver"""
    driver = webdriver.Chrome()  # Or your preferred WebDriver
    healenium_test = HealeniumTestCase(driver, request.config.healenium_db)
    healenium_test.current_test_name = request.node.name
    yield healenium_test
    driver.quit()


# Sample test cases
class TestLoginPage:
    def test_login_form(self, healenium):
        """Test login form with self-healing locators"""
        healenium.driver.get("https://acme-test.uipath.com/login")

        # Find username field
        username = healenium.find_element(
            By.ID, "email",
            element_name="Login Username Field"
        )
        username.send_keys("vikic3110@gmail.com")

        # Find password field
        password = healenium.find_element(
            By.ID, "password",
            element_name="Login Password Field"
        )
        password.send_keys("Amaze789!")

        # Find login button
        login_btn = healenium.find_element(
            By.XPATH, "//button[@type='submit']",
            element_name="Login Submit Button"
        )
        login_btn.click()

        # # Assert successful login
        # welcome_msg = healenium.find_element(
        #     By.CLASS_NAME, "welcome-message",
        #     element_name="Welcome Message"
        # )
        # assert welcome_msg.is_displayed()


# class TestSearchFunction:
#     def test_search_results(self, healenium):
#         """Test search functionality with self-healing locators"""
#         healenium.driver.get("https://acme-test.uipath.com/login")
#
#         # Find search input
#         search_input = healenium.find_element(
#             By.ID, "email",
#             element_name="email test Field"
#         )
#         search_input.send_keys("vikic3110@gmail.com")
#
#         # Find search button
#         password_input = healenium.find_element(
#             By.XPATH, "//input[@name='password']",
#             password_input="password text field"
#         )
#         search_input.send_keys("Amaze789!")


        # Verify results
        # login_btn = healenium.find_element(
        #     By.XPATH, "//button[@type='submit']",
        #     element_name="Login Button"
        # )
        # login_btn.click()


# Custom test result collector
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    result = outcome.get_result()

    if result.when == "call":
        item.config.healenium_results.append({
            'test_name': item.name,
            'status': result.outcome,
            'timestamp': datetime.now(),
        })


def run_tests():
    """Function to run tests and return results"""
    # Run pytest programmatically
    pytest.main([
        __file__,
        '-v',
        '--capture=no'
    ])


if __name__ == "__main__":
    run_tests()