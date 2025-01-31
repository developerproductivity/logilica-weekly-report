import base64
from datetime import datetime, timezone
from io import StringIO
import logging
from pathlib import Path
import unittest
from unittest import mock
from unittest.mock import MagicMock

from googleapiclient.errors import HttpError
import platformdirs
import yaml

from logilica_weekly_report.update_gdoc import (
    APPLICATION_NAME,
    DEFAULT_APP_CREDENTIALS_FILE_NAME,
    DEFAULT_GDRIVE_FILE_TEMPLATE,
    DEFAULT_TOKEN_FILE_NAME,
    generate_html,
    get_app_credentials_file,
    get_google_credentials,
    get_token_file,
    upload_doc,
)

CUT = "logilica_weekly_report.update_gdoc."

DEFAULT_CONFIGS = (
    """---
config:
""",
    """---
config:
  google:
""",
    """---
config:
  google:
    "useless key": "useless value"
""",
)


class TestUpdateGDoc(unittest.TestCase):
    def test_get_token_file_default_results(self):
        expected_dir = platformdirs.user_cache_path(APPLICATION_NAME)
        expected = expected_dir / DEFAULT_TOKEN_FILE_NAME

        for entry in DEFAULT_CONFIGS:
            config = yaml.safe_load(StringIO(entry))
            result = get_token_file(config)
            self.assertEqual(expected, result)

    def test_get_token_file_partial_dir(self):
        for entry in ("subdir/", "subdir1/subdir2/"):
            config = {"google": {"token_file": entry}}
            result = get_token_file(config)
            expected_dir = platformdirs.user_cache_path(entry[:-1])
            expected = expected_dir / DEFAULT_TOKEN_FILE_NAME
            self.assertEqual(expected, result)

    def test_get_token_file_full_dir(self):
        for entry in ("./", "./subdir/", "/opt/config/"):
            config = {"google": {"token_file": entry}}
            result = get_token_file(config)
            expected = Path(entry) / DEFAULT_TOKEN_FILE_NAME
            self.assertEqual(expected, result)

    def test_get_token_file_with_no_dir(self):
        expected_dir = platformdirs.user_cache_path(APPLICATION_NAME)
        for entry in ("my_token.json",):
            config = {"google": {"token_file": entry}}
            expected = expected_dir / entry
            result = get_token_file(config)
            self.assertEqual(expected, result)

    def test_get_token_file_no_dir(self):
        for entry, expected_dir in (
            ("./my_token.json", Path(".")),
            ("partial_dir/my_token.json", platformdirs.user_cache_path("")),
            ("/opt/subdir/my_token.json", Path("")),
        ):
            config = {"google": {"token_file": entry}}
            expected = expected_dir / entry
            result = get_token_file(config)
            self.assertEqual(expected, result)

    def test_get_app_credentials_file_default_results(self):
        expected_dir = platformdirs.user_config_path(APPLICATION_NAME)
        expected = expected_dir / DEFAULT_APP_CREDENTIALS_FILE_NAME

        for entry in DEFAULT_CONFIGS:
            config = yaml.safe_load(StringIO(entry))
            result = get_app_credentials_file(config)
            self.assertEqual(expected, result)

    def test_get_app_credentials_file_partial_dir(self):
        for entry in ("subdir/", "subdir1/subdir2/"):
            config = {"google": {"app_credentials_file": entry}}
            result = get_app_credentials_file(config)
            expected_dir = platformdirs.user_config_path(entry[:-1])
            expected = expected_dir / DEFAULT_APP_CREDENTIALS_FILE_NAME
            self.assertEqual(expected, result)

    def test_get_app_credentials_file_full_dir(self):
        for entry in ("./", "./subdir/", "/opt/config/"):
            config = {"google": {"app_credentials_file": entry}}
            result = get_app_credentials_file(config)
            expected = Path(entry) / DEFAULT_APP_CREDENTIALS_FILE_NAME
            self.assertEqual(expected, result)

    def test_get_app_credentials_file_with_no_dir(self):
        expected_dir = platformdirs.user_config_path(APPLICATION_NAME)
        for entry in ("my_token.json",):
            config = {"google": {"app_credentials_file": entry}}
            expected = expected_dir / entry
            result = get_app_credentials_file(config)
            self.assertEqual(expected, result)

    def test_app_credentials_file_no_dir(self):
        for entry, expected_dir in (
            ("./my_app_credentials.json", Path(".")),
            ("partial_dir/my_app_credentials.json", platformdirs.user_config_path("")),
            ("/opt/subdir/my_app_credentials.json", Path("")),
        ):
            config = {"google": {"app_credentials_file": entry}}
            expected = expected_dir / entry
            result = get_app_credentials_file(config)
            self.assertEqual(expected, result)

    @mock.patch(CUT + "open", new_callable=unittest.mock.mock_open)
    @mock.patch(CUT + "InstalledAppFlow")
    @mock.patch(CUT + "Credentials")
    @mock.patch(CUT + "get_app_credentials_file")
    @mock.patch(CUT + "get_token_file")
    def test_get_google_credentials(
        self,
        mock_get_token_file,
        mock_get_app_credentials_file,
        mock_credentials,
        mock_installedappflow,
        mock_open,
    ):
        # Create mocks objects to be returned by mock functions
        mock_token_file = MagicMock()
        mock_app_credentials_file = MagicMock()
        mock_cached_creds = MagicMock()
        mock_flow = MagicMock()
        mock_new_creds = MagicMock()

        # Set mock functions to return the mock objects
        mock_get_token_file.return_value = mock_token_file
        mock_get_app_credentials_file.return_value = mock_app_credentials_file
        mock_cached_creds.to_json.return_value = MagicMock()
        mock_credentials.from_authorized_user_file.return_value = mock_cached_creds
        mock_installedappflow.from_client_secrets_file.return_value = mock_flow
        mock_new_creds.to_json.return_value = MagicMock()
        mock_flow.run_local_server.return_value = mock_new_creds

        def check_creds_are_generated_and_saved(expected, actual):
            self.assertEqual(expected, actual)
            mock_cached_creds.refresh.assert_not_called()
            mock_open.assert_called_with(mock_token_file, "w")
            mock_open().write.assert_called_with(expected.to_json.return_value)
            # Reset for next scenario
            mock_open().write.reset_mock()

        # Scenario 1:  token file exists; cached creds are good; creds are not
        # refreshed, not generated, and not saved.
        mock_token_file.exists.return_value = True
        mock_cached_creds.valid = True
        result = get_google_credentials({})
        self.assertEqual(mock_cached_creds, result)
        mock_cached_creds.refresh.assert_not_called()
        mock_flow.run_local_server.assert_not_called()
        mock_open.assert_not_called()

        # Scenario 2:  no creds in existing token file; new creds are generated
        # and saved.
        mock_get_token_file.exists.return_value = True
        mock_credentials.from_authorized_user_file.return_value = None
        result = get_google_credentials({})
        check_creds_are_generated_and_saved(mock_new_creds, result)
        # Reset for next scenario
        mock_credentials.from_authorized_user_file.return_value = mock_cached_creds

        # Scenario 3:  have token, invalid, expired; have refresh token; creds
        # are refreshed and saved.
        mock_get_token_file.exists.return_value = True
        mock_cached_creds.valid = False
        mock_cached_creds.expired = True
        mock_cached_creds.refresh_token = True
        result = get_google_credentials({})
        self.assertEqual(mock_cached_creds, result)
        mock_cached_creds.refresh.assert_called()
        mock_open.assert_called_with(mock_token_file, "w")
        mock_open().write.assert_called_with(mock_cached_creds.to_json.return_value)
        # Reset for next scenario
        mock_open().write.reset_mock()
        mock_cached_creds.reset_mock()

        # Scenario 4:  token file exists; creds not valid, not expired; creds
        # are generated and saved.
        mock_get_token_file.exists.return_value = True
        mock_cached_creds.expired = False
        result = get_google_credentials({})
        check_creds_are_generated_and_saved(mock_new_creds, result)

        # Scenario 5:  token file exists; creds not valid, expired, but have no
        # refresh token; creds are generated and saved.
        mock_get_token_file.exists.return_value = True
        mock_cached_creds.expired = True
        mock_cached_creds.refresh_token = False
        result = get_google_credentials({})
        check_creds_are_generated_and_saved(mock_new_creds, result)

        # Scenario 6:  token file does not exist; creds are generated and saved.
        mock_get_token_file.exists.return_value = False
        result = get_google_credentials({})
        check_creds_are_generated_and_saved(mock_new_creds, result)

    @mock.patch(CUT + "datetime")
    @mock.patch(CUT + "MediaIoBaseUpload")
    @mock.patch(CUT + "build")
    def test_upload_doc(
        self,
        mock_build,
        mock_mediaiobaseupload,
        mock_datetime,
    ):
        expected_id = "mock ID string"
        frozen_time = datetime.now(tz=timezone.utc)

        mock_doc = MagicMock()
        mock_creds = MagicMock()
        mock_request = MagicMock()
        mock_status = MagicMock()
        mock_response = MagicMock()

        mock_doc.encode.return_value = bytes(
            "This is an HTML document", encoding="utf-8"
        )
        handle_create = mock_build().files().create
        handle_create.return_value = mock_request
        mock_request.next_chunk.return_value = (mock_status, mock_response)
        mock_status.progress.return_value = 1.0
        mock_response.get.return_value = expected_id
        mock_datetime.now.return_value = frozen_time

        def check_result(expected_file_name, result_id):
            self.assertEqual(expected_id, result_id)
            actual_file = handle_create.call_args.kwargs.get("body", {}).get("name")
            self.assertEqual(expected_file_name, actual_file)
            # Reset for next scenario
            handle_create.reset_mock()
            mock_status.progress.reset_mock(side_effect=True)

        # Scenario 1:  default target filename
        expected_file = DEFAULT_GDRIVE_FILE_TEMPLATE.format(frozen_time)
        result = upload_doc(mock_doc, mock_creds, {})
        check_result(expected_file, result)

        # Scenario 2:  default target filename, partial config
        expected_file = DEFAULT_GDRIVE_FILE_TEMPLATE.format(frozen_time)
        result = upload_doc(mock_doc, mock_creds, {"google": {}})
        check_result(expected_file, result)

        # Scenario 3:  custom target filename
        expected_file = "output_file.html"
        config = {"google": {"filename": expected_file}}
        result = upload_doc(mock_doc, mock_creds, config)
        check_result(expected_file, result)

        # Scenario 4:  custom target filename with template
        file_template = "output_file_{:%Y-%m}"
        expected_file = file_template.format(frozen_time)
        config = {"google": {"filename": expected_file}}
        result = upload_doc(mock_doc, mock_creds, config)
        check_result(expected_file, result)

        # Scenario 5:  multiple chunk upload
        mock_status.progress.side_effect = (0.33, 0.67, 1.0)
        mock_request.next_chunk.side_effect = (
            (mock_status, None),
            (mock_status, None),
            (mock_status, mock_response),
        )
        result = upload_doc(mock_doc, mock_creds, {})
        self.assertEqual(expected_id, result)
        # Reset for next scenario
        handle_create.reset_mock()
        mock_status.progress.reset_mock(side_effect=True)

        # Scenario 6:  upload failure
        mock_response.reason = "mock reason"
        mock_request.next_chunk.side_effect = HttpError(
            mock_response, b"mock upload error"
        )
        logging.getLogger().setLevel(logging.CRITICAL)  # Suppress the error message
        with self.assertRaises(HttpError):
            _ = upload_doc(mock_doc, mock_creds, {})
        self.assertEqual(expected_id, result)
        handle_create.reset_mock()
        mock_status.progress.reset_mock(side_effect=True)

    def test_generate_html(self):
        # Test scenarios with zero, one, and two teams, and zero, one, and two
        # dashboards.
        scenarios = (
            {},
            {
                "team1": {"team1-dashboard1": b"This is image t1d1."},
            },
            {
                "team2": {"team2-dashboard1": b"This is image t2d1."},
                "team3": {"team3-dashboard1": b"This is image t3d1."},
            },
            {
                "team4": {},
            },
            {
                "team5": {
                    "team5-dashboard1": b"This is image t5d1.",
                    "team5-dashboard2": b"This is image t5d2.",
                },
            },
        )

        for scenario in scenarios:
            result = generate_html(scenario).getvalue()
            self.assertTrue(
                result.startswith(
                    "<!DOCTYPE html><html><body><h1>Logilica Weekly Report</h1>"
                )
            )
            for team, dashboards in scenario.items():
                self.assertTrue(f"<hr><h2>{team}</h2>" in result)
                for image in dashboards.values():
                    image_data = base64.b64encode(image).decode()
                    self.assertTrue(
                        f'<img src="data:image/png;base64,{image_data}' in result
                    )


if __name__ == "__main__":
    unittest.main()
