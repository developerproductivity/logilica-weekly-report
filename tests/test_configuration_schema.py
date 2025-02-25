from copy import deepcopy
from io import StringIO
from typing import Any, Generator
import unittest

from jsonschema import ValidationError
import yaml

from logilica_weekly_report.configuration_schema import validate_configuration

FULL_CONFIG = yaml.safe_load(
    StringIO(
        """---
teams:
  My Awesome Team:
    team_dashboards:
      Team Productivity Dashboard:
        filename: sample_report.pdf
        url: some-string
integrations:
  foobar-bot:
    connector: GitHub
    membership_repositories:
      - my_org/my-repo
      - my_org/my-repo-2
    public_repositories:
      - my-public-org/my-repo
  foobar-public-bot:
    connector: GitHub
    public_repositories:
      - my-public-org/my-repo
config:
  google:
    app_credentials_file: path/to/file
    token_file: path/to/file
"""
    )
)


def recursive_descent_removal(
    removals: dict[str, Any],
    cfg: dict[str, Any],
    original_config: dict[str, Any],
    mkey: str,
) -> Generator[dict[str, Any], None, None]:
    """Recursively descend the tree of missing fields, removing them from the
    configuration where indicated, yielding the result, and then restoring them
    again.

    `cfg` must refer to a subtree of `original_config`, so that when `cfg` is
    modified, the result appears in `original_config`.
    """
    for k, v in removals.items():
        if k == mkey:
            continue

        if k not in cfg:
            raise AssertionError(
                f"Test bug: key {k!s} not found in {cfg} inside {original_config}"
            )

        if mkey in v:
            save = cfg[k]
            del cfg[k]
            yield original_config
            cfg[k] = save

        yield from recursive_descent_removal(v, cfg[k], original_config, mkey)


def generate_valid_configs() -> Generator[dict[str, Any], None, None]:
    """A generator which yields a sequence of valid configurations."""
    # Exactly one root-level key present.
    for k, v in FULL_CONFIG.items():
        yield {k: v}

    # Exactly one root-level key absent from the full configuration, or one
    # missing optional field.
    mkey = "remove_this_key"
    missing = {
        "teams": {mkey: True},
        "integrations": {
            mkey: True,
            next(iter(FULL_CONFIG["integrations"])): {
                "public_repositories": {mkey: True},
                "membership_repositories": {mkey: True},
            },
        },
        "config": {
            mkey: True,
            "google": {
                "app_credentials_file": {mkey: True},
                "token_file": {mkey: True},
            },
        },
    }

    # Create a copy of the configuration which the subroutine will modify and
    # yield.
    config = deepcopy(FULL_CONFIG)
    yield from recursive_descent_removal(missing, config, config, mkey)
    assert config == deepcopy(FULL_CONFIG)  # Make sure we cleaned up properly.


def recursive_descent_add(
    extra: dict[str, Any],
    cfg: dict[str, Any],
    original_config: dict[str, Any],
    e_key: str,
) -> Generator[dict[str, Any], None, None]:
    """Recursively descend the tree of extraneous fields, adding them to the
    configuration where indicated, yielding the result, and then removing them
    again.

    `cfg` must refer to a subtree of `original_config`, so that when `cfg` is
    modified, the result appears in `original_config`.
    """
    for k, v in extra.items():
        if k == e_key:
            cfg[k] = v
            yield original_config
            del cfg[k]
        elif k in cfg:
            yield from recursive_descent_add(v, cfg[k], original_config, e_key)
        else:
            raise AssertionError(
                f"Test bug: key {k!s} not found in {cfg} inside {original_config}"
            )


def generate_extraneous_keys() -> Generator[dict[str, Any], None, None]:
    """A generator which yields a sequence of configurations which are invalid
    because they contain extraneous fields where they are not permitted.
    """

    # This config tree mirrors the structure of the full config tree with extra
    # fields added in places where they are not permitted; the test will
    # generate configurations by adding single fields from this tree to the
    # full configuration.  These are the locations of the extra fields:
    #   - root-level key
    #   - under "teams.XXX"
    #   - under "teams.XXX.team_dashboards.YYY"
    #   - under "integrations.XXX"
    #   - under "config"
    #   - under "config.google"
    first_team = next(iter(FULL_CONFIG["teams"]))
    first_dashboard = next(iter(FULL_CONFIG["teams"][first_team]["team_dashboards"]))
    e_key = "extraneous_key"
    extraneous = {
        e_key: "extraneous_value",
        "teams": {
            first_team: {
                e_key: "extraneous_value",
                "team_dashboards": {first_dashboard: {e_key: "extraneous_value"}},
            }
        },
        "integrations": {
            next(iter(FULL_CONFIG["integrations"])): {e_key: "extraneous_value"}
        },
        "config": {e_key: "extraneous_value", "google": {e_key: "extraneous_value"}},
    }

    # Create a copy of the configuration which the inner function will modify
    # and yield.
    config = deepcopy(FULL_CONFIG)
    yield from recursive_descent_add(extraneous, config, config, e_key)
    assert config == deepcopy(FULL_CONFIG)  # Make sure we cleaned up properly.


def generate_missing_fields() -> Generator[dict[str, Any], None, None]:
    """A generator which yields a sequence of configurations which are invalid
    because they are missing required fields.
    """

    # This config tree mirrors the structure of the full config tree with
    # markers added to indicate fields which should be removed for testing; the
    # test will generate configurations by removing the indicated fields from
    # the full configuration.  These are the locations of the fields:
    #   - "teams.XXX.team_dashboards"
    #   - "teams.XXX.team_dashboards.YYY.filename"
    #   - "teams.XXX.team_dashboards.YYY.url"
    #   - "integrations.XXX.connector"
    first_team = next(iter(FULL_CONFIG["teams"]))
    first_dashboard = next(iter(FULL_CONFIG["teams"][first_team]["team_dashboards"]))
    mkey = "remove_this_key"
    missing = {
        "teams": {
            first_team: {
                "team_dashboards": {
                    mkey: True,
                    first_dashboard: {
                        "filename": {mkey: True},
                        "url": {mkey: True},
                    },
                }
            }
        },
        "integrations": {
            next(iter(FULL_CONFIG["integrations"])): {"connector": {mkey: True}}
        },
    }

    # Create a copy of the configuration which the subroutine will modify and
    # yield.
    config = deepcopy(FULL_CONFIG)
    yield from recursive_descent_removal(missing, config, config, mkey)
    assert config == deepcopy(FULL_CONFIG)  # Make sure we cleaned up properly.


def recursive_descent_replacement(
    mods: dict[str, Any],
    cfg: dict[str, Any],
    original_config: dict[str, Any],
    r_key: str,
) -> Generator[dict[str, Any], None, None]:
    """Recursively descend the tree of to-be-replaced fields, replacing their
    values where indicated in the configuration, yielding the result, and then
    restoring them again.

    `cfg` must refer to a subtree of `original_config`, so that when `cfg` is
    modified, the result appears in `original_config`.
    """
    for k, v in mods.items():
        if k == r_key:
            continue

        if k not in cfg:
            raise AssertionError(
                f"Test bug: key {k!s} not found in {cfg} inside {original_config}"
            )

        if r_key in v:
            save = cfg[k]
            cfg[k] = v[r_key]
            yield original_config
            cfg[k] = save

        yield from recursive_descent_replacement(v, cfg[k], original_config, r_key)


def generate_questionable_configs() -> Generator[dict[str, Any], None, None]:
    """A generator which yields a sequence of configurations which are have
    questionable validity because one of their fields is present but contains
    an empty value.
    """

    # This config tree mirrors the structure of the full config tree with
    # markers for fields whose values should be replaced in the config for
    # testing; the test will generate configurations by replacing the indicated
    # fields' values with the specified values in the full configuration, then
    # the values will be restored for the next generation.  These are the
    # locations of the fields:
    #   - "teams", "integrations", "config" present with no (i.e., empty) value
    #   - "teams.XXX.team_dashboards" present with no (i.e., empty) value
    #   - "integrations.XXX.public_repositories" present with no (i.e., empty) value
    #   - "integrations.XXX.membership_repositories" present with no (i.e., empty) value
    #   - "config.google" present with no (i.e., empty) value

    first_team = next(iter(FULL_CONFIG["teams"]))
    first_integration = next(iter(FULL_CONFIG["integrations"]))
    q_key = "replace_this_value"
    replacements = {
        "teams": {
            q_key: {},
            first_team: {"team_dashboards": {q_key: {}}},
        },
        "integrations": {
            q_key: {},
            first_integration: {
                "public_repositories": {q_key: []},
                "membership_repositories": {q_key: []},
            },
        },
        "config": {
            q_key: {},
            "google": {q_key: {}},
        },
    }

    # Create a copy of the configuration which the subroutine will modify and
    # yield.
    config = deepcopy(FULL_CONFIG)
    yield from recursive_descent_replacement(replacements, config, config, q_key)
    assert config == deepcopy(FULL_CONFIG)  # Make sure we cleaned up properly.


def generate_bad_types() -> Generator[dict[str, Any], None, None]:
    """A generator which yields a sequence of configurations which are invalid
    because one of their fields contains the wrong type of data.
    """

    # This config tree mirrors the structure of the full config tree with
    # markers for fields whose values should be replaced in the config for
    # testing; the test will generate configurations by replacing the indicated
    # fields' values with the specified values in the full configuration, then
    # the values will be restored for the next generation.  These are the
    # locations of the fields:
    #   - "teams"
    #   - "teams.XXX"
    #   - "teams.XXX.team_dashboards"
    #   - "teams.XXX.team_dashboards.YYY"
    #   - "teams.XXX.team_dashboards.YYY.filename"
    #   - "teams.XXX.team_dashboards.YYY.url"
    #   - "integrations"
    #   - "integrations.XXX"
    #   - "integrations.XXX.connector"
    #   - "integrations.XXX.public_repositories"
    #   - "integrations.XXX.membership_repositories"
    #   - "config"
    #   - "config.google"
    #   - "config.google.app_credentials_file"
    #   - "config.google.token_file"
    first_team = next(iter(FULL_CONFIG["teams"]))
    first_dashboard = next(iter(FULL_CONFIG["teams"][first_team]["team_dashboards"]))
    first_integration = next(iter(FULL_CONFIG["integrations"]))
    b_key = "replace_this_value"
    replacements = {
        "teams": {
            b_key: 1,
            first_team: {
                b_key: 1,
                "team_dashboards": {
                    b_key: 1,
                    first_dashboard: {
                        b_key: 1,
                        "filename": {b_key: 1},
                        "url": {b_key: 1},
                    },
                },
            },
        },
        "integrations": {
            b_key: 1,
            first_integration: {
                b_key: 1,
                "connector": {b_key: 1},
                "public_repositories": {b_key: 1},
                "membership_repositories": {b_key: 1},
            },
        },
        "config": {
            b_key: 1,
            "google": {
                b_key: 1,
                "app_credentials_file": {b_key: 1},
                "token_file": {b_key: 1},
            },
        },
    }

    # Create a copy of the configuration which the subroutine will modify and
    # yield.
    config = deepcopy(FULL_CONFIG)
    yield from recursive_descent_replacement(replacements, config, config, b_key)
    assert config == deepcopy(FULL_CONFIG)  # Make sure we cleaned up properly.


class TestConfigurationSchema(unittest.TestCase):

    def test_valid_configurations(self):
        count = 0

        def do_it(gen):
            nonlocal count
            for config in gen:
                validate_configuration(config)
                count += 1

        do_it(generate_valid_configs())
        self.assertEqual(10, count)
        do_it(generate_questionable_configs())
        self.assertEqual(10 + 7, count)

    def test_invalid_configurations(self):
        count = 0

        def do_it(gen, exp):
            nonlocal count
            for config in gen:
                with self.assertRaises(ValidationError) as cm:
                    validate_configuration(config)
                self.assertIn(exp, str(cm.exception))
                count += 1

        do_it(
            generate_extraneous_keys(),
            "Additional properties are not allowed ('extraneous_key' was unexpected)",
        )
        do_it(
            generate_missing_fields(),
            "is a required property",
        )
        do_it(
            generate_bad_types(),
            "is not of type",
        )
        self.assertEqual(25, count)


if __name__ == "__main__":
    unittest.main()
