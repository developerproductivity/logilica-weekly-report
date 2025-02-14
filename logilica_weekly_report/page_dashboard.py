import logging
import pathlib
from typing import Any

from playwright.sync_api import Page


class DashboardPage:
    def __init__(self, page: Page):
        self.page = page
        self.export_pdf_button = page.get_by_role("button", name="Export PDF")
        self.download_button = page.get_by_role("button", name="Download").nth(1)
        self.close_download_button = page.get_by_role("button", name="Close").nth(1)

    def download_dashboard_to(self, path: pathlib.Path) -> None:
        self.export_pdf_button.click()
        # download file and close the dialog afterwards
        with self.page.expect_download() as download_info:
            self.download_button.click()
            download = download_info.value
            download.save_as(path)
            self.close_download_button.click()
        logging.debug("Download stored in '%s'", path)

    def download_team_dashboards(
        self,
        teams: dict[str, Any],
        base_dir_path: pathlib.Path,
        *,
        menu_dropdown="Custom Reports",
    ) -> None:
        for team, dashboards in teams.items():
            for dashboard, options in dashboards["team_dashboards"].items():
                logging.debug(
                    "Downloading dashboard '%s / %s' for team '%s'",
                    menu_dropdown,
                    dashboard,
                    team,
                )
                self.page.goto(url=options["url"])
                self.download_dashboard_to(path=base_dir_path / options["filename"])

            logging.info(
                "Downloaded %d dashboard%s for '%s' team",
                len(dashboards["team_dashboards"]),
                "s" if len(dashboards["team_dashboards"]) > 1 else "",
                team,
            )
