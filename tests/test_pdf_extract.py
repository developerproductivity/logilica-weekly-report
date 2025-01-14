import pathlib
import unittest

from logilica_weekly_report.pdf_extract import get_pdf_objects


class MyTestCase(unittest.TestCase):
    def test_get_pdf_objects(self):
        config = {
            "Mock Team": {
                "team_dashboards": {
                    "Mock Team Dashboard": {"Filename": "sample_report.pdf"}
                }
            }
        }

        result = get_pdf_objects(config, pathlib.Path(__file__).parent / "fixtures")
        self.assertEqual(
            3,
            len(result["Mock Team"]["Mock Team Dashboard"]["text"]),
            "Unexpected number of text sections found.",
        )
        self.assertEqual(
            5,
            len(result["Mock Team"]["Mock Team Dashboard"]["images"]),
            "Unexpected number of images sections found.",
        )


if __name__ == "__main__":
    unittest.main()
