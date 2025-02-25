import logging
from typing import Optional

from playwright.sync_api import Page, TimeoutError


class NavigationPanel:
    """Page Object to handle interactions with Navigation Panel on the left."""

    DROPDOWN_TIMEOUT = 3000

    def __init__(self, page: Page):
        self.page = page

    def navigate(self, *, menu_dropdown: Optional[str], link_name: str) -> None:
        """Opens a link in navigation panel.

        Opens a link, opens a dropdown first if provided.
        """

        logging.debug(
            "Navigating to '%s%s'",
            f"{menu_dropdown} / " if menu_dropdown else "",
            link_name,
        )

        link_locator = self.page.get_by_role("link", name=link_name)

        # if dropdown argument was provided, check if dropdown is open as it hides the link
        if menu_dropdown:
            for first_try in (True, False):
                try:
                    link_locator.wait_for(
                        state="visible", timeout=self.DROPDOWN_TIMEOUT
                    )
                    break
                except TimeoutError:
                    if not first_try:
                        raise

                    logging.debug("Opening dropdown '%s' first", menu_dropdown)
                    self.page.get_by_role("link", name=menu_dropdown).click()

        # open link
        link_locator.click()
