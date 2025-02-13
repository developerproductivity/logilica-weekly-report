#
# This module contains support functions which extract text and image objects
# from a PDF file for inclusion in other media.
#
import logging
import pathlib
from typing import Any, NamedTuple

import pymupdf

# Choosing a higher image DPI produces a finer quality image but a larger
# amount of data; it also affects the sizes of the headers and footers; so,
# everything is parameterized by SCALE.
REPORT_HEADER_HEIGHT = 94
PAGE_HEADER_HEIGHT = 12
PAGE_FOOTER_HEIGHT = 43


def get_pdf_objects(
    teams: dict[str, dict[str, Any]],
    download_dir_path: pathlib.Path,
) -> dict[str, dict[str, bytes]]:
    """Extract content from the configured PDF files.

    Assumes that the teams configuration is a dictionary whose keys are the
    teams' names (e.g., "Practices Team") and whose values are dictionaries
    reflecting the following YAML:
        Practices Team:
          team_dashboards:
            Developer Practices Dashboard:
              filename: DPROD_Report.pdf
            DPROD Dashboard 2:
              filename: DPROD_Report2.pdf
            ...
        ...

    Returns a hierarchical set of dictionaries:
      - the first level keys are the teams' names
      - the second level keys are the Dashboard names
      - the values are the contents of the Dashboards as PNG images
    """
    results = {}
    for team, dashboards in teams.items():
        team_results = {}
        for dashboard, options in dashboards["team_dashboards"].items():
            logging.info("Extracting items from '%s' for %s", dashboard, team)
            pdf: pymupdf.Document
            with pymupdf.open(download_dir_path / options["filename"]) as pdf:
                team_results[dashboard] = get_report_image(pdf)
        results[team] = team_results
    return results


def get_report_image(pdf: pymupdf.Document) -> bytes:
    """Render the PDF, with the pages knitted together, as a single image.

    The individual pages' pixmaps are copied to adjacent locations in the
    target pixmap.  In the process, page headers, footers, and trailing
    whitespace are omitted.  The pixmap is returned as a byte-string.
    """

    class PageArea(NamedTuple):
        offset: int
        length: int
        pixmap: pymupdf.Pixmap

    # Calculate and record the length required for each page; track the total
    # length.
    page_areas: list[PageArea] = []
    total_length = 0
    for i, page in enumerate(iter(pdf)):
        offset = REPORT_HEADER_HEIGHT if i == 0 else PAGE_HEADER_HEIGHT
        pix: pymupdf.Pixmap = page.get_pixmap()
        pl = strip_trailing_space(pix) - offset
        page_areas.append(PageArea(offset, pl, pix))
        total_length += pl

    # Google Docs have a maximum image size of 2500 pixels in either dimension,
    # so, we need to resize the result accordingly.
    if total_length > 2500:
        logging.warning(
            "Dashboard image height (%s pixels) exceeds the Google Docs limit of 2500",
            total_length,
        )

    # Create the target pixmap based on the characteristics of the first page
    # and the total length of all the pages.
    base_pixmap = page_areas[0].pixmap
    d_image = pymupdf.Pixmap(
        base_pixmap.colorspace,
        (0, 0, base_pixmap.width, total_length),
        base_pixmap.alpha,
    )

    # Locate each page region and copy it to the appropriate place in the
    # destination pixmap.
    dest_start = 0
    for pa in page_areas:
        pix = pa.pixmap
        pix.set_origin(0, dest_start - pa.offset)
        dest_end = dest_start + pa.length
        dest_rect = (0, dest_start, pix.width, dest_end)
        d_image.copy(pix, dest_rect)
        dest_start = dest_end

    logging.debug(
        "Resulting image size (%d dpi):  %d x %d (pixels);   %0.2f x %0.2f (inches)",
        d_image.xres,
        d_image.width,
        d_image.height,
        d_image.width / d_image.xres,
        d_image.height / d_image.yres,
    )
    return d_image.tobytes(output="png")


def strip_trailing_space(pix: pymupdf.Pixmap) -> int:
    """Returns the height coordinate of the last row of pixels which is
    different from the first row of the footer; assuming that the first row of
    the footer is "blank", this returns the height at which to truncate the
    pixmap to remove the trailing whitespace.
    """
    # The pixmap is structured as a linear serialization of a three-dimensional
    # array of pixels: "height" rows, by "width" columns, by 'n' items
    # representing (e.g.) red, green, blue, and transparency values as integers.
    # The stride indicates how many items are in a single row.  Find the index
    # of the first row of the footer (which we assume is blank), and grab a
    # reference to it.
    stride: int = pix.stride
    footer_row_idx: int = (pix.height - PAGE_FOOTER_HEIGHT) * stride
    blank_row = pix.samples_mv[footer_row_idx : footer_row_idx + stride]

    # Starting at the last row before the footer, work backwards looking for a
    # row whose values are different from those of a "blank" row.
    for pos in range(footer_row_idx - stride, 0, -stride):
        if pix.samples_mv[pos : pos + stride] != blank_row:
            return pos // stride

    raise ValueError("Page appears to be blank!")
