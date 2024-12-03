#
# This module contains support functions which extract text and image objects
# from a PDF file for inclusion in other media.
#
from typing import Any, Union

from PIL.PngImagePlugin import ImageFile
from pypdf import PdfReader

PDF_ITEMS = dict[str, Union[list[str], dict[str, ImageFile]]]


def get_pdf_objects(
    config: dict[str, dict[str, Any]]
) -> dict[str, dict[str, PDF_ITEMS]]:
    """Extract all images and text from the configured PDF files.

    Assumes that the configuration reflects the following YAML:
        teams:
          Practices Team:
            team_dashboards:
              Developer Practices Dashboard:
                Filename: DPROD_Report.pdf
              ...
          ...
        config:
          Download_path: "downloaded_pdfs/"
    """
    results = {}
    for team, dashboards in config["teams"].items():
        team_results = {}
        for dashboard, options in dashboards["team_dashboards"].items():
            dashboard_results = {"images": {}, "text": []}
            pdf = PdfReader(config["config"]["Download_path"] + options["Filename"])
            for page in pdf.pages:
                i = {image.name: image.image for image in page.images}
                t = page.extract_text(
                    extraction_mode="layout",
                    layout_mode_space_vertically=False,
                )
                dashboard_results["images"].update(i)
                dashboard_results["text"].append(t)
            team_results[dashboard] = dashboard_results
        results[team] = team_results
    return results
