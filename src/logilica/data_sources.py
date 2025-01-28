import click

# Default values for command options
DEFAULT_CONFIG_FILE = "./weekly_report.yaml"
DEFAULT_DOWNLOADS_DIR = "./lwr_downloaded_pdfs"


@click.command(
    epilog="For more information, see https://github.com/developerproductivity/logilica-weekly-report#logilica-weekly-report"
)
@click.pass_context
def data_sources(
    context: click.Context,
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

    configuration = context["configuration"]
    pass

    context.exit(exit_status)
