import unittest

from src.pdf_extract import get_pdf_objects


class MyTestCase(unittest.TestCase):
    def test_get_pdf_objects(self):
        config = {
            "teams": {
                "Mock Team": {
                    "team_dashboards": {"Mock Team Dashboard": {"Filename": "test.pdf"}}
                }
            },
            "config": {"Download_path": "tests/fixtures/"},
        }
        result = get_pdf_objects(config)
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
