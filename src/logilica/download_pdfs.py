import logging
import pathlib
from typing import Any

from playwright.sync_api import Page

from logilica.playwright_session import PlaywrightSession
from logilica.pages.login_page import LoginPage


def download_pdfs(
    teams: dict[str, Any],
    credentials: dict[str, Any],
    download_dir_path: pathlib.Path,
) -> None:
    """Download a PDF file for each team's report using the Logilica Web UI."""
    with PlaywrightSession() as page:
        # Fill the login form using environment variables
        logging.info("Logging into Logilica")

        login_page = LoginPage(page=page, configuration=teams, credentials=credentials)
        login_page.open()
        login_page.login()

        page.get_by_role("link", name="Custom Reports").click()
        export_pdfs(teams, page, download_dir_path)


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
