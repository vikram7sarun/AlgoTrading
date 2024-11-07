import datetime
import logging
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pdb


def test_search_functionality(healenium):
    """Test search functionality with debug capabilities"""
    try:
        logging.info("Starting search functionality test")

        # Debug point - before navigation
        # breakpoint()

        healenium.driver.get("https://duckduckgo.com")
        logging.debug("Navigated to DuckDuckGo")
        breakpoint()
        # Find search input
        search_input = healenium.find_element(
            By.ID, "search_form_input_homepage",
            element_name="Search Input"
        )
        logging.debug("Found search input")

        # Enter search term
        search_input.send_keys("Selenium automation")
        logging.debug("Entered search term")

        # Find and click search button
        search_button = healenium.find_element(
            By.ID, "search_button_homepage",
            element_name="Search Button"
        )
        search_button.click()
        logging.debug("Clicked search button")

        # Verify results
        results = WebDriverWait(healenium.driver, 10).until(
            EC.presence_of_element_located((By.ID, "links"))
        )
        assert results.is_displayed(), "Search results should be visible"
        logging.info("Test completed successfully")

    except Exception as e:
        logging.error(f"Test failed: {str(e)}")
        screenshot_path = os.path.join(
            "screenshots",
            f"failure_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        healenium.driver.save_screenshot(screenshot_path)
        raise


def test_healing_demonstration(healenium):
    """Demonstrate self-healing capabilities"""
    try:
        logging.info("Starting healing demonstration test")

        healenium.driver.get("https://duckduckgo.com")

        # Try with incorrect ID to trigger healing
        search_input = healenium.find_element(
            By.ID, "incorrect_search_input_id",
            element_name="Search Input with Healing"
        )

        search_input.send_keys("Test automation")
        logging.debug("Successfully found and used healed element")

        # Verify element interaction worked
        value = search_input.get_attribute("value")
        assert value == "Test automation", "Search input value verification failed"
        logging.info("Test completed successfully")

    except Exception as e:
        logging.error(f"Test failed: {str(e)}")
        screenshot_path = os.path.join(
            "screenshots",
            f"failure_healing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        healenium.driver.save_screenshot(screenshot_path)
        raise


def test_form_interaction(healenium):
    """Test form interactions with multiple elements"""
    try:
        logging.info("Starting form interaction test")

        healenium.driver.get("https://the-internet.herokuapp.com/login")

        # Find username field
        username = healenium.find_element(
            By.ID, "username",
            element_name="Username Field"
        )
        username.send_keys("tomsmith")

        # Find password field
        password = healenium.find_element(
            By.ID, "password",
            element_name="Password Field"
        )
        password.send_keys("SuperSecretPassword!")

        # Find login button
        login_button = healenium.find_element(
            By.CSS_SELECTOR, "button[type='submit']",
            element_name="Login Button"
        )
        login_button.click()

        # Verify successful login
        success_message = healenium.find_element(
            By.CLASS_NAME, "flash.success",
            element_name="Success Message"
        )
        assert "You logged into a secure area!" in success_message.text
        logging.info("Test completed successfully")

    except Exception as e:
        logging.error(f"Test failed: {str(e)}")
        screenshot_path = os.path.join(
            "screenshots",
            f"failure_form_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        healenium.driver.save_screenshot(screenshot_path)
        raise


def test_search_functionality(healenium):
    """Test search functionality with proper screenshot handling"""
    try:
        logging.info("Starting search functionality test")

        healenium.driver.get("https://duckduckgo.com")
        logging.debug("Navigated to DuckDuckGo")

        # Find search input
        search_input = healenium.find_element(
            By.ID, "search_form_input_homepage",
            element_name="Search Input"
        )

        search_input.send_keys("Selenium automation")

        # Find and click search button
        search_button = healenium.find_element(
            By.ID, "search_button_homepage",
            element_name="Search Button"
        )
        search_button.click()

        # Verify results
        results = WebDriverWait(healenium.driver, 10).until(
            EC.presence_of_element_located((By.ID, "links"))
        )
        assert results.is_displayed(), "Search results should be visible"

    except Exception as e:
        logging.error(f"Test failed: {str(e)}")

        # Create screenshots directory if it doesn't exist
        os.makedirs("screenshots", exist_ok=True)

        # Save screenshot with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_path = os.path.join(
            "screenshots",
            f"failure_search_{timestamp}.png"
        )
        healenium.driver.save_screenshot(screenshot_path)

        # Record screenshot in database
        cursor = healenium.db_conn.cursor()
        cursor.execute('SELECT MAX(id) FROM locators')
        last_locator_id = cursor.fetchone()[0]

        if last_locator_id:
            healenium._record_screenshot(screenshot_path, last_locator_id)

        raise


def test_sample_elements(healenium):
    """Test case to generate sample data for UI"""
    try:
        # Navigate to test site
        healenium.driver.get("https://the-internet.herokuapp.com/login")

        # Test valid locator
        username = healenium.find_element(
            By.ID, "username",
            element_name="Username Field"
        )
        username.send_keys("test_user")

        # Test locator that needs healing
        try:
            password = healenium.find_element(
                By.ID, "wrong_password_id",
                element_name="Password Field"
            )
        except:
            password = healenium.find_element(
                By.ID, "password",
                element_name="Password Field"
            )
        password.send_keys("test_pass")

        # Test another valid locator
        login_button = healenium.find_element(
            By.CSS_SELECTOR, "button[type='submit']",
            element_name="Login Button"
        )
        login_button.click()

    except Exception as e:
        logging.error(f"Test failed: {str(e)}")
        screenshot_path = os.path.join(
            "screenshots",
            f"failure_sample_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        healenium.driver.save_screenshot(screenshot_path)
        raise

if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])