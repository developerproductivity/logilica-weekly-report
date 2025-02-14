from collections import defaultdict
import logging
from typing import Any, Generator, Optional, Tuple, TypeAlias

from playwright.sync_api import expect, Locator, Page

from logilica_weekly_report.page_navigation import NavigationPanel

IntegrationSyncFailures: TypeAlias = dict[Tuple[str, str], list[Tuple[str, str]]]


class SettingsPage:
    """Page Object to handle interactions with Logilica Settings.

    Provides interactions with Settings / Integrations.
    """

    IMPORTED_REPOSITORY_TIMEOUT = 9000
    AVAILABLE_REPOSITORY_TIMEOUT = IMPORTED_REPOSITORY_TIMEOUT * 6

    def __init__(self, page: Page):

        self.page = page
        self.add_public_repository_dialog_button = page.get_by_role(
            "button", name="Add Public Repository"
        )
        self.add_public_repository_confirm_button = page.get_by_role(
            "button", name="Add Project"
        )
        self.search_imported_repos_field = page.locator(
            "input[placeholder='Search repository...']"
        ).nth(0)
        self.search_available_repos_field = page.locator(
            "input[placeholder='Search repository...']"
        ).nth(1)
        self.add_public_repository_input = page.locator(
            "label:has-text('Repo URL') + input"
        )

    def open_integration_configuration(self, integration: str, connector: str) -> None:
        """Opens Integration Configuration.

        Opens Integration configuration. Assumes that Settings/Integrations is
        opened prior to that.
        """

        logging.debug(
            "Opening integration '%s', connector type:'%s'", integration, connector
        )
        self.page.locator("div.items-center").filter(has_text=connector).filter(
            has_text=integration
        ).get_by_role("button", name="Configure").click()
        expect(
            self.page.get_by_role("heading", name=f"{connector} Settings")
        ).to_be_visible()

    def wait_for_available_repositories(
        self,
        repositories: list[str],
    ) -> Generator[str, None, None]:
        """Waits for Integration / Settings / Available Repositories and
        afterwards yields the list of repositories.
        """
        if repositories:
            logging.debug(
                "Waiting up to %d milliseconds for membership repositories to appear on the screen prior starting adding them.",
                self.AVAILABLE_REPOSITORY_TIMEOUT,
            )
            self.page.wait_for_timeout(self.AVAILABLE_REPOSITORY_TIMEOUT)
            yield from repositories

    def process_public_repositories(
        self,
        connector: str,
        integration_name: str,
        repositories: list[str],
        failures: IntegrationSyncFailures,
    ) -> None:
        """Adds all repositories into connector setup as public repositories.

        Args:
          connector:
            connector type, e.g. GitHub
          integration_name:
            integration name, e.g. account_botname
          repositories:
            repositories to be added
          failures:
            failures object, will be updated in case of failures
        """
        added_repositories: list[str] = []
        for repo_slug in repositories:
            if not self.has_repository_imported(repo_slug):
                self.add_public_repository(repo_slug)
                added_repositories.append(repo_slug)

        missing_repositories = self.check_imported_repositories(added_repositories)
        if missing_repositories:
            failures[(connector, integration_name)].extend(missing_repositories)

    def process_membership_repositories(
        self,
        connector: str,
        integration_name: str,
        repositories: list[str],
        failures: IntegrationSyncFailures,
    ) -> None:
        """Adds all repositories into connector setup as membership
        repositories.
        """

        added_repositories = []
        for repo_slug in self.wait_for_available_repositories(repositories):
            if not self.has_repository_imported(repo_slug):
                if self.add_membership_repository(repo_slug):
                    added_repositories.append(repo_slug)
                else:
                    failures[(connector, integration_name)].append(
                        (
                            repo_slug,
                            f"❌ Repository {repo_slug} was not among available repositories",
                        )
                    )
        missing_repositories = self.check_imported_repositories(added_repositories)
        if missing_repositories:
            failures[(connector, integration_name)].extend(missing_repositories)

    def sync_integrations(self, integrations: dict[str, Any]) -> None:
        """Synchronizes integration configuration from file to UI.

        Updates Logilica integration configuration for all connectors specified
        in integrations sections of the local configuration file.

        Raises:
          RuntimeError: If any repositories could not have been added to the configuration.
        """

        sync_failures: IntegrationSyncFailures = defaultdict(list)
        for integration_name, details in integrations.items():
            connector = details["connector"]
            public_repos = details.get("public_repositories", [])
            member_repos = details.get("membership_repositories", [])
            logging.debug(
                "Syncing integration '%s' (connector '%s'), "
                "%d public repositories, %d membership based repositories",
                integration_name,
                connector,
                len(public_repos),
                len(member_repos),
            )

            # open configuration UI
            NavigationPanel(self.page).navigate(
                link_name="Integrations", menu_dropdown="Settings"
            )
            self.open_integration_configuration(
                integration=integration_name, connector=connector
            )

            # process public repositories
            self.process_public_repositories(
                connector=connector,
                integration_name=integration_name,
                repositories=public_repos,
                failures=sync_failures,
            )
            # process membership repositories
            self.process_membership_repositories(
                connector=connector,
                integration_name=integration_name,
                repositories=member_repos,
                failures=sync_failures,
            )

        if sync_failures:
            logging.error(
                "There are failures for %d integrations in syncing sources",
                len(sync_failures),
            )
            for (connector, name), failures in sync_failures.items():
                logging.error("Failures in connector %s named '%s':", connector, name)
                for repo, f in failures:
                    logging.error("%s: %s", repo, f)
            raise RuntimeError(sync_failures)

    def has_repository_imported(self, repository_slug: str) -> bool:
        """Checks if a repository is visible in imported repository UI."""
        self.search_imported_repos_field.fill(repository_slug)

        # here we need to find the innermost div element that exactly matches repository slug
        if self.repository_slug_locator(repository_slug).nth(0).is_visible():
            logging.debug("✅ Repository '%s' is imported", repository_slug)
            return True

        return False

    def check_imported_repositories(self, repositories: list[str]) -> list[(str, str)]:
        """Checks if repositories are visible in imported repository UI.

        Returns:
          A list of tuples (repository slug, failure) representing errors,
          empty list otherwise.
        """
        if not repositories:
            return []

        logging.debug(
            "Waiting %d milliseconds for %d newly added repositories to be reflected in the UI",
            self.IMPORTED_REPOSITORY_TIMEOUT,
            len(repositories),
        )
        # we should not run a generic wait however the UI doesn't give us other option
        self.page.wait_for_timeout(self.IMPORTED_REPOSITORY_TIMEOUT)
        missing_repositories = [
            (added_repo, f"❌ Repository {added_repo} was not imported.")
            for added_repo in repositories
            if not self.has_repository_imported(added_repo)
        ]
        return missing_repositories

    def add_public_repository(
        self, repository_slug: str, *, host="https://github.com"
    ) -> None:
        """Adds repository as public repository."""

        logging.debug("⏳ Adding public repository '%s/%s.git'", host, repository_slug)
        self.add_public_repository_dialog_button.click()
        self.add_public_repository_input.fill(f"{host}/{repository_slug}.git")
        self.add_public_repository_confirm_button.click()
        # as UI refresh is triggered independently of the click and there is no guarantee the repository will be added
        # at the top of the page, we don't validate the action success here and always consider it successful

    def add_membership_repository(self, repository_slug: str) -> bool:
        """Adds repository as membership repository."""

        logging.debug("⏳ Adding membership repository '%s'", repository_slug)
        self.search_available_repos_field.fill(repository_slug)
        locator = self.repository_control_button(repository_slug, order=1)
        if locator:
            locator.click()
            self.page.get_by_text("Add", exact=True).click()
            return True

        return False

    def repository_control_button(
        self, repository_slug: str, *, order=0
    ) -> Optional[Locator]:
        """Finds repository control button.

        Finds repository control button. Since there might be multiple buttons
        (up to 2), provides additional logic to pick up the right one.  The
        first button might be found in imported repositories, the other one in
        available repositories.

        Args:
          repository_slug:
            git slug that identifies the repository, e.g. org_name/repo_name
          order: optional
            identifies what button is returned if 2 are found (by default the
            first one, indexed from 0)

        Returns:
          Control button.

        Raises:
          RuntimeError: in case more than 2 buttons are found.
        """

        # let's find the row that lists specific repository slug
        # in that row, there is a hamburger button
        locator = (
            self.page.get_by_role("row", name=repository_slug)
            .filter(has=self.page.get_by_text(text=repository_slug, exact=True))
            .get_by_role("button")
        )

        # there might be the same slug in both imported repositories and available repositories
        # in that case, we want to be able to select one specifically
        count = locator.count()
        if count == 1:
            return locator
        if count == 2:
            return locator.nth(order)
        if count > 2:
            raise RuntimeError(
                f"There should be up to 2 rows with {repository_slug} however the script has found {locator.count()} instead. Details {str(locator)}"
            )

        return None

    def repository_slug_locator(self, slug: str) -> Locator:
        """Locator for repository slug element."""

        # here we need to find the innermost div element that exactly matches repository slug
        # alternative option is to use an xpath selector that is more powerful. Leaving it
        # in the code in case it will be needed because of DOM tree changes
        # self.page.locator(f"//div[normalize-space()='{slug}' and not(descendant::div)]")
        return self.page.get_by_text(text=slug, exact=True)
