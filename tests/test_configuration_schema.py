from io import StringIO
import unittest

from jsonschema import ValidationError
import yaml

from logilica_weekly_report.configuration_schema import validate_configuration

VALID_CONFIGS = (
    """---
teams:
  My Awesome Team:
    team_dashboards:
      Team Productivity Dashboard:
        filename: Awesome.pdf
        url: some-string
integrations:
  foobar-bot:
    connector: GitHub
    membership_repositories:
      - myorg/my-repo
      - myorg/my-repo-2
  foobar-public-bot:
    connector: GitHub
    public_repositories:
      - my-public-org/my-repo
config:
  google:
    app_credentials_file: path/to/file
    token_file: path/to/file
""",
    """---
teams:
  My Awesome Team:
    team_dashboards:
      Team Productivity Dashboard:
        filename: Awesome.pdf
        url: some-string
integrations:
  foobar-public-bot:
    connector: GitHub
    public_repositories:
      - my-public-org/my-repo
""",
    """---
config:
  google:
    app_credentials_file: path/to/file
    token_file: path/to/file
""",
)

INVALID_CONFIGS = (
    """---
teams:
  My Awesome Team:
    team_dashboards:
      Team Productivity Dashboard:
        filename: 1
        not-url: some-string
integrations:
  foobar-bot:
    connector: GitHub
    membership_repositories:
      - 2
      - myorg/my-repo-2
  foobar-public-bot:
    connector: GitHub
    public_repositories:
      - my-public-org/my-repo
config:
  google:
    app_credentials_file: path/to/file
    token_file: True
""",
    """---
integrations:
  foobar-public-bot:
    connector: GitHub
    public_repositories:
      - 2
""",
    """---
config:
  google:
    app_credentials_file: path/to/file
    token_file: 42
""",
)


class TestConfigurationSchema(unittest.TestCase):
    def test_valid_configurations(self):
        for entry in VALID_CONFIGS:
            config = yaml.safe_load(StringIO(entry))
            validate_configuration(config)

    def test_invalid_configurations(self):
        for entry in INVALID_CONFIGS:
            config = yaml.safe_load(StringIO(entry))
            with self.assertRaises(ValidationError):
                validate_configuration(config)


if __name__ == "__main__":
    unittest.main()
