from selenium.webdriver.common.by import By


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


class TestSearchFunction:
    def test_search_results(self, healenium):
        """Test search functionality with self-healing locators"""
        healenium.driver.get("https://example.com/search")

        # Find search input
        search_input = healenium.find_element(
            By.ID, "search-box",
            element_name="Search Input Field"
        )
        search_input.send_keys("test product")

        # Find search button
        search_btn = healenium.find_element(
            By.XPATH, "//button[@type='submit']",
            element_name="Search Submit Button"
        )
        search_btn.click()

        # Verify results
        results = healenium.find_element(
            By.CLASS_NAME, "search-results",
            element_name="Search Results Container"
        )
        assert results.is_displayed()