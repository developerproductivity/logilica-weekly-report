import logging
import os
import pathlib
import shutil

import click

from logilica.download_pdfs import download_pdfs
from logilica.pdf_extract import get_pdf_objects
from logilica.update_gdoc import update_gdoc

# Default values for command options
DEFAULT_DOWNLOADS_DIR = "./la_downloaded_pdfs"


@click.command(
    epilog="For more information, see https://github.com/developerproductivity/logilica-weekly-report#logilica-weekly-report"
)
@click.option(
    "--downloads",
    "-d",
    "download_dir_path",
    type=click.Path(
        writable=True, file_okay=False, path_type=pathlib.Path, resolve_path=True
    ),
    default=DEFAULT_DOWNLOADS_DIR,
    show_default=True,
    help="Path to a directory to receive downloaded files"
    " (will be created if it doesn't exist; will be deleted if created)",
)
@click.pass_context
def weekly_report(
    context: click.Context,
    download_dir_path: pathlib.Path,
) -> None:
    """A tool for fetching Logilica reports, extracting their contents, and
    adding them to a Google Doc.

    \f

    The main function for the `logilica-weekly-report` tool

    Using the Click support, we parse the command line, extract the
    configuration information, store some of it in the Click context, and then
    get about business.
    """
    exit_status = 0
    configuration = context.obj["configuration"]
    credentials = context.obj["credentials"]

    remove_downloads = not download_dir_path.exists()
    logging.debug(
        "download directory %s", "does not exist" if remove_downloads else "exists"
    )
    if remove_downloads:
        os.mkdir(download_dir_path)
        logging.info("download directory, %s, created", download_dir_path)

    try:
        download_pdfs(
            teams=configuration["teams"],
            credentials=credentials,
            download_dir_path=download_dir_path,
        )
        pdf_items = get_pdf_objects(
            teams=configuration["teams"], download_dir_path=download_dir_path
        )
        update_gdoc(pdf_items, configuration["config"])
    except Exception as err:
        click.echo(err, err=True)
        exit_status = 1
    finally:
        if remove_downloads:
            logging.info("removing downloads directory")
            shutil.rmtree(download_dir_path)

    context.exit(exit_status)
