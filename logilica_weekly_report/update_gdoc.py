import base64
from datetime import datetime
from io import BytesIO
import logging
from pathlib import Path
from typing import Callable, Literal, Optional, Union

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
import platformdirs
from yattag import Doc, SimpleDoc

APPLICATION_NAME = "Logilica"
DEFAULT_APP_CREDENTIALS_FILE_NAME = "application_default_credentials.json"
DEFAULT_GDRIVE_FILE_TEMPLATE = "Logilica_Reports_{:%Y-%m-%d}"
DEFAULT_TOKEN_FILE_NAME = "token.json"


def generate_html(pdf_items: dict[str, dict[str, bytes]]) -> SimpleDoc:
    """Generate an HTML document from the set of charts and text extracted from
    the PDF.
    """
    doc, tag, text = Doc().tagtext()
    doc.asis("<!DOCTYPE html>")
    with tag("html"):
        with tag("body"):
            with tag("h1"):
                text("Logilica Weekly Report")
            add_teams(pdf_items, doc, tag, text)
    return doc


def add_teams(
    pdf_items: dict[str, dict[str, bytes]],
    doc: SimpleDoc,
    tag: Callable[[str], SimpleDoc.Tag],
    text: Callable[[str], None],
):
    """Add sections to the document for each team.

    The dashboard images are inserted into the document as data URIs.
    """
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


def upload_doc(doc: str, creds: Credentials, config: dict[str, any]) -> str:
    """Upload the provided in-memory HTML document to Google Drive.

    The file is created on the Google Drive with a MIME type of
    `'application/vnd.google-apps.document'`, which causes Google to treat it
    as or convert it to a GDoc.
    """

    filename = (
        config.get("google", {})
        .get("filename", DEFAULT_GDRIVE_FILE_TEMPLATE)
        .format(datetime.now())
    )
    file_metadata = {
        "name": filename,
        "mimeType": "application/vnd.google-apps.document",
    }
    try:
        service = build("drive", "v3", credentials=creds)
        media = MediaIoBaseUpload(
            BytesIO(doc.encode()), mimetype="text/html", resumable=True
        )
        request = service.files().create(
            body=file_metadata,
            fields="id",
            media_body=media,
            includeLabels=None,
            includePermissionsForView=None,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Uploaded {int(status.progress() * 100)}%.")
        logging.info(
            'File "%s" with ID "%s" has been uploaded.', filename, response.get("id")
        )

    except HttpError as error:
        logging.error("An error occurred uploading %s: %s", filename, error)
        raise

    return response.get("id")


def get_google_credentials(config: dict[str, any]) -> Credentials:
    """Get the Google OAuth credentials needed to use Google Drive.

    The token is obtained either using values cached in a local file or by
    prompting the user to perform an authorization dialog; either way, the
    new token is written to the cache file before returning.

    The Google OAuth 2.0 Client "app" configuration is constructed from a local
    credentials file (which can be downloaded from https://console.developers.google.com,
    under "Credentials").  It is located using the default mechanisms (e.g., in
    ${HOME}/.config/gcloud/application_default_credentials.json).  (Currently,
    the scope of the authorization is limited to the Google Drive APIs.)
    """
    token_file = get_token_file(config)
    logging.debug("Google OAuth token file: %s", token_file)
    app_credentials_file = get_app_credentials_file(config)
    logging.debug("Google app credentials file: %s", app_credentials_file)
    scopes = ["https://www.googleapis.com/auth/drive.file"]

    creds = None
    # The token file stores the user's access and refresh tokens and is created
    # automatically when the authorization flow completes for the first time.
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logging.info("Refreshing credentials.")
            creds.refresh(Request())
            logging.debug("Credentials refreshed successfully.")
        else:
            # Lead the user through a login using the browser
            logging.info("Launching OAuth login dialog.")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(app_credentials_file), scopes
            )
            creds = flow.run_local_server(port=0)
            logging.debug("OAuth login successful.")
        # Save the credentials for the next run
        with open(token_file, "w") as token:
            logging.info("Caching OAuth tokens.")
            token.write(creds.to_json())
    return creds


def get_token_file(config: dict[str, any]) -> Path:
    """Get the Path to the file for caching the OAuth tokens."""
    return get_info_file(
        config.get("google", {}).get("token_file"),
        DEFAULT_TOKEN_FILE_NAME,
        platformdirs.user_cache_path,
    )


def get_app_credentials_file(config: dict[str, any]) -> Path:
    """Get the file containing the Google Client app credentials."""
    return get_info_file(
        config.get("google", {}).get("app_credentials_file"),
        DEFAULT_APP_CREDENTIALS_FILE_NAME,
        platformdirs.user_config_path,
    )


GPP_SIGNATURE = Callable[
    [Optional[str], Optional[Union[str, Literal[False]]], Optional[str], bool, bool],
    Path,
]


def get_info_file(
    config_string: Optional[str],
    default_file_name: Optional[str],
    get_platform_path: GPP_SIGNATURE,
) -> Path:
    """Generate the file path, based on the tool configuration with supplied
    defaults for the file name and platform directory locations, creating the
    parent directories if necessary.
    """

    if not config_string:
        config_string = ""

    # The pathlib handling doesn't discriminate well between files and
    # directories -- they are all "paths" (e.g., it strips superfluous slashes,
    # including trailing ones) -- so, if the input string ends in a slash, take
    # it all as the directory path; otherwise, assume the last "part" is a file
    # name.
    filename = ""
    ipath = Path(config_string)
    if not config_string.endswith("/"):
        filename = ipath.name
        ipath = ipath.parent
    # Treat relative paths as relative to the platform's conventional location;
    # however, if the path starts with an explicit references to the current
    # working directory, use it as is.
    if not ipath.is_absolute() and not config_string.startswith("./"):
        # If the path includes a directory, use it the "application name";
        # otherwise (in which case pathlib will report the parent as ".") use
        # the default application name.
        app_name = str(ipath) if str(ipath) != "." else APPLICATION_NAME
        # noinspection PyArgumentList
        ipath = get_platform_path(app_name, ensure_exists=True)
    ipath /= filename if filename else default_file_name
    return ipath
