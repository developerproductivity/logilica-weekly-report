import logging
import os
import pathlib
import shutil

import click
import yaml

from logilica_weekly_report.download_pdfs import check_download_setup, download_pdfs
from logilica_weekly_report.pdf_extract import get_pdf_objects
from logilica_weekly_report.update_gdoc import update_gdoc

# Default values for command options
DEFAULT_CONFIG_FILE = "./weekly_report.yaml"
DEFAULT_DOWNLOADS_DIR = "./lwr_downloaded_pdfs"

# Set up logging and create the Bottle application
logging.basicConfig(format="[%(levelname)s] lwr: %(message)s", level=logging.WARNING)


@click.command(
    epilog="For more information, see https://github.com/developerproductivity/logilica-weekly-report#logilica-weekly-report"
)
@click.option(
    "--config",
    "-C",
    "config_file_path",
    type=click.Path(
        exists=True, dir_okay=False, path_type=pathlib.Path, resolve_path=True
    ),
    default=DEFAULT_CONFIG_FILE,
    show_default=True,
    help="Path to configuration file",
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
@click.option(
    "--pwdebug",
    "--PWD",
    "-D",
    is_flag=True,
    required=False,
    default=False,
    help="Enable Playwright debug mode",
)
@click.option(
    "--verbose",
    "-v",
    count=True,
    help="Enable verbose mode; specify multiple times to increase verbosity",
)
@click.pass_context
def cli(
    context: click.Context,
    config_file_path: pathlib.Path,
    download_dir_path: pathlib.Path,
    pwdebug: bool,
    verbose: int,
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

    if verbose:
        logging.getLogger().setLevel(logging.INFO if verbose == 1 else logging.DEBUG)
        logging.debug("Debug mode enabled")

    if pwdebug:
        # Playwright debug mode requested:  enable Playwright debug support.
        os.environ["PWDEBUG"] = "1"
        logging.debug("Playwright debug mode enabled")

    logging.info(
        "config path: '%s';\n\tdownload path: '%s'", config_file_path, download_dir_path
    )

    err = check_download_setup()
    if err:
        click.echo(err, err=True)
        context.exit(2)

    with open(config_file_path, "r") as yaml_file:
        configuration = yaml.safe_load(yaml_file)
        logging.debug("configuration: %s", str(configuration))

    remove_downloads = not download_dir_path.exists()
    logging.debug(
        "download directory %s", "does not exist" if remove_downloads else "exists"
    )
    if remove_downloads:
        os.mkdir(download_dir_path)
        logging.info("download directory, %s, created", download_dir_path)

    try:
        download_pdfs(configuration["teams"], download_dir_path)
        pdf_items = get_pdf_objects(configuration["teams"], download_dir_path)
        update_gdoc(pdf_items, configuration["config"])
    except Exception as err:
        click.echo(err, err=True)
        exit_status = 1
    finally:
        if remove_downloads:
            logging.info("removing downloads directory")
            shutil.rmtree(download_dir_path)

    context.exit(exit_status)


if __name__ == "__main__":
    cli()
