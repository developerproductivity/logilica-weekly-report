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
                            "properties": {"Filename": {"type": "string"}},
                        },
                    },
                    "jira_projects": {"type": "string"},
                },
            },
        },
        "integrations": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "type": {"type": "string"},
                    "repositories": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            },
        },
        "config": {
            "oneOf": [
                {"type": "object", "additionalProperties": False},
                {"type": "null"},
            ],
            "description": "Configuration section (not used now)",
        },
    },
    "required": ["teams", "integrations", "config"],
}
