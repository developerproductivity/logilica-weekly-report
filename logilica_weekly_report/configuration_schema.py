import logging
from typing import Any

from jsonschema import validate

schema = {
    "type": "object",
    "properties": {
        "teams": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "team_dashboards": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "filename": {"type": "string"},
                                "url": {"type": "string"},
                            },
                            "required": ["filename", "url"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["team_dashboards"],
                "additionalProperties": False,
            },
        },
        "integrations": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "connector": {"type": "string"},
                    "public_repositories": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "membership_repositories": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["connector"],
                "additionalProperties": False,
            },
        },
        "config": {
            "type": "object",
            "properties": {
                "google": {
                    "type": "object",
                    "properties": {
                        "app_credentials_file": {
                            "type": "string",
                            "description": "Path to the Google app credentials file",
                        },
                        "token_file": {
                            "type": "string",
                            "description": "Path to the Google OAuth token file",
                        },
                    },
                    "additionalProperties": False,
                },
            },
            "additionalProperties": False,
        },
    },
    "additionalProperties": False,
}


def validate_configuration(configuration: Any) -> None:
    """Validates configuration (parsed YAML) against schema.

    Raises:
      ValidationError:
        In case configuration is not valid against schema
    """
    validate(instance=configuration, schema=schema)
    logging.debug("valid configuration: %s", str(configuration))
