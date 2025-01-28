import logging

from typing import Any
from playwright.sync_api import expect

from logilica.pages.base_page import BasePage


class LoginPage(BasePage):
    LOGILICA_LOGIN = "https://logilica.io/login"

    def __init__(
        self, page, configuration: dict[str, Any], credentials: dict[str, Any]
    ):
        super().__init__(page)
        self.configuration: dict[str, Any] = configuration
        self.credentials: dict[str, Any] = credentials

    def open(self):
        self.goto(self.LOGILICA_LOGIN)

    def login(self):

        # Fill the login form using environment variables
        logging.info("Logging into Logilica")
        self.page.get_by_role("button", name="Log in With Email").click()
        self.page.locator("#domain").fill(self.credentials["domain"])
        self.page.locator("#email").fill(self.credentials["username"])
        self.page.locator("#password").fill(self.credentials["password"])
        self.page.get_by_role("button", name="Login").click()

        try:
            expect(self.page).not_to_have_url(self.LOGILICA_LOGIN)
        except AssertionError:
            logging.error("Login failed")
            raise ValueError("Login credentials rejected")
        logging.debug("Login to Logilica complete")
