from typing import Optional

from playwright.sync_api import BrowserContext, Page, sync_playwright


class PlaywrightSession:
    """Encapsulation of Playwright Browser for usage in Page Objects."""

    def __init__(self, headless=True):
        self.headless = headless
        self.browser = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.context = self.browser.new_context(accept_downloads=True)
        self.page = self.context.new_page()
        return self.page

    def __exit__(self, exc_type, exc_value, traceback):
        self.browser.close()
        self.playwright.stop()
