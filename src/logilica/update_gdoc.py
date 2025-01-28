import base64
from typing import Callable

from yattag import Doc, SimpleDoc


def update_gdoc(pdf_items: dict[str, dict[str, bytes]], config: dict[str, any]) -> None:
    """Take the set of charts and text extracted from the PDF and insert it
    into the Google Doc.

    This is accomplished by generating an HTML document and uploading it to
    Google Drive with a MIME type of `'application/vnd.google-apps.document'`,
    which causes Google to treat/convert it to a GDoc.  The images are inserted
    into it as data URIs, which Google will manage appropriately.
    """

    doc, tag, text = Doc().tagtext()

    doc.asis("<!DOCTYPE html>")
    with tag("html"):
        with tag("body"):
            with tag("h1"):
                text("Logilica Weekly Report")
                add_teams(pdf_items, doc, tag, text)

    print(doc.getvalue())


def add_teams(
    pdf_items: dict[str, dict[str, bytes]],
    doc: SimpleDoc,
    tag: Callable[[str], SimpleDoc.Tag],
    text: Callable[[str], None],
):
    for team, dashboards in pdf_items.items():
        doc.asis("<hr>")
        with tag("h2"):
            text(team)
        for dashboard, contents in dashboards.items():
            image_data = base64.b64encode(contents).decode()
            doc.stag(
                "img",
                src="data:image/png;base64," + image_data,
                width="80%",
                height="80%",
            )
