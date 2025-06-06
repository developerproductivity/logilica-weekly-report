import logging
import os
import pathlib

import click
from click import Command
from jsonschema import ValidationError
import yaml

from logilica_cli import sort_click_command_parameters
from logilica_cli.configuration_schema import validate_configuration
from logilica_cli.data_sources import data_sources
from logilica_cli.weekly_report import weekly_report

# Default values for command options
DEFAULT_CONFIG_FILE = "./logilica-cli.yaml"
DEFAULT_OUTPUT_DIR = "./output"

# Set up logging and create the Bottle application
logging.basicConfig(
    format="[%(levelname)s] logilica-cli: %(message)s", level=logging.WARNING
)


@sort_click_command_parameters
@click.group(
    epilog="For more information, see https://github.com/developerproductivity/logilica-cli#logilica-cli"
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
    "--output-dir",
    "-o",
    "output_dir_path",
    type=click.Path(
        writable=True, file_okay=False, path_type=pathlib.Path, resolve_path=True
    ),
    default=DEFAULT_OUTPUT_DIR,
    show_default=True,
    help="Path to a directory to store output if image-only output is selected",
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
    output_dir_path: str,
    pwdebug: bool,
    verbose: int,
) -> None:
    """A tool to automate UI interactions with Logilica.

    \f

    The main command group for `Logilica UI` automation tool.

    Using the Click support, we parse the command line, extract the
    configuration information, store some of it in the Click context, and then
    pass it to other commands that interact with the UI using Playwright.
    """

    if verbose:
        logging.getLogger().setLevel(logging.INFO if verbose == 1 else logging.DEBUG)
        logging.debug("Debug mode enabled")

    if pwdebug:
        # Playwright debug mode requested:  enable Playwright debug support.
        os.environ["PWDEBUG"] = "1"
        logging.debug("Playwright debug mode enabled")

    with open(config_file_path, "r") as yaml_file:
        configuration = yaml.safe_load(yaml_file)
        try:
            validate_configuration(configuration)
        except ValidationError as e:
            logging.error("Invalid Configuration: %s", str(configuration))
            click.echo(f"Invalid YAML configuration: {e}", err=True)
            context.exit(5)

    context.ensure_object(dict)
    context.obj["configuration"] = configuration
    context.obj["output_dir_path"] = output_dir_path


command: Command
for command in [weekly_report, data_sources]:
    cli.add_command(command)

if __name__ == "__main__":
    cli()
