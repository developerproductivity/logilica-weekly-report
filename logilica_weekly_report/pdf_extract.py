#
# This module contains support functions which extract text and image objects
# from a PDF file for inclusion in other media.
#
import logging
import pathlib
from typing import Any, Union

from PIL.PngImagePlugin import ImageFile
from pypdf import PdfReader

PDF_ITEMS = dict[str, Union[list[str], dict[str, ImageFile]]]


def get_pdf_objects(
    teams_config: dict[str, dict[str, Any]],
    download_path: pathlib.Path,
) -> dict[str, dict[str, PDF_ITEMS]]:
    """Extract all images and text from the configured PDF files.

    Assumes that the teams configuration is a dictionary whose keys are the
    teams' names (e.g., "Practices Team") and whose values are dictionaries
    reflecting the following YAML:
        Practices Team:
          team_dashboards:
            Developer Practices Dashboard:
              Filename: DPROD_Report.pdf
            ...
        ...

    Returns a hierarchical set of dictionaries:
      - the first level keys are the teams' names
      - the second level keys are the Dashboard names
      - the third level keys are "images" or "text"
      - the value of the "images" key is a mapping of image names to JPEG contents
      - the value of the "text" key is a list of text blobs
    """
    results = {}
    for team, dashboards in teams_config.items():
        team_results = {}
        for dashboard, options in dashboards["team_dashboards"].items():
            logging.debug("Extracting items from '%s' for %s", dashboard, team)
            dashboard_results = {"images": {}, "text": []}
            pdf = PdfReader(download_path / options["Filename"])
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
