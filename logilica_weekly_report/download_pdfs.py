import logging
import os
import pathlib
from typing import Optional

from playwright.sync_api import Page, sync_playwright

LOGILICA_LOGIN = "https://logilica.io/login"


def check_download_setup() -> Optional[str]:
    """Check that we have what we need; return an error message on failure or
    None on success.
    """
    for e in ("LOGILICA_DOMAIN", "LOGILICA_EMAIL", "LOGILICA_PASSWORD"):
        if not os.getenv(e):
            return f"Environment variable '{e}' is not set"


def download_pdfs(teams_config: dict[str, any], download_path: pathlib.Path) -> None:
    """Download a PDF file for each team's report using the Logilica Web UI."""
    with sync_playwright() as playwright:
        with playwright.chromium.launch(headless=True) as browser:
            with browser.new_context(accept_downloads=True) as context:
                page = context.new_page()

                # Fill the login form using environment variables
                logging.info("Logging into Logilica")
                page.goto(LOGILICA_LOGIN)
                page.get_by_role("button", name="Log in With Email").click()
                page.locator("#domain").fill(os.getenv("LOGILICA_DOMAIN"))
                page.locator("#email").fill(os.getenv("LOGILICA_EMAIL"))
                page.locator("#password").fill(os.getenv("LOGILICA_PASSWORD"))
                page.get_by_role("button", name="Login").click()

                if page.url == LOGILICA_LOGIN:
                    logging.error("Login failed")
                    raise ValueError("Login credentials rejected")
                logging.debug("Login to Logilica complete")

                page.get_by_role("link", name="Custom Reports").click()
                export_pdfs(teams_config, page, download_path)


def export_pdfs(
    teams_config: dict[str, any], page: Page, download_path: pathlib.Path
) -> None:
    """Cycle though the list of team dashboards to download a PDF for each
    team.
    """
    for team, dashboards in teams_config.items():
        for dashboard, options in dashboards["team_dashboards"].items():
            logging.info("Downloading '%s' for %s", dashboard, team)
            page.get_by_role("link", name=dashboard).click()
            page.get_by_role("button", name="Export PDF").click()
            # Handle download
            with page.expect_download() as download_info:
                page.get_by_role("button", name="Download").nth(1).click()
                download = download_info.value
                download.save_as(download_path / options["Filename"])
                # Close PDF view dialog
                page.get_by_role("button", name="Close").nth(1).click()
            logging.debug("Downloading '%s' complete", dashboard)
