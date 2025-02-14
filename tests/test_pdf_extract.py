import pathlib
import unittest

from logilica_weekly_report.pdf_extract import get_pdf_objects


class MyTestCase(unittest.TestCase):
    def test_get_pdf_objects(self):
        config = {
            "Mock Team": {
                "team_dashboards": {
                    "Mock Team Dashboard": {"filename": "sample_report.pdf"}
                }
            }
        }

        result = get_pdf_objects(config, pathlib.Path(__file__).parent / "fixtures")
        self.assertEqual(
            1,
            len(result),
            "Unexpected number of teams found.",
        )
        self.assertEqual(
            1,
            len(result["Mock Team"]),
            "Unexpected number of dashboards found.",
        )
        self.assertEqual(
            175526,
            len(result["Mock Team"]["Mock Team Dashboard"]),
            "Unexpected images size found.",
        )


if __name__ == "__main__":
    unittest.main()
