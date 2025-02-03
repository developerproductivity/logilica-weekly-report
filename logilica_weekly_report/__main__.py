import logging
import os
import pathlib

import click
from jsonschema import validate, ValidationError
import yaml

from logilica_weekly_report.cli_data_sources import data_sources
from logilica_weekly_report.cli_weekly_report import weekly_report
from logilica_weekly_report.configuration_schema import schema

# Default values for command options
DEFAULT_CONFIG_FILE = "./weekly_report.yaml"

# Set up logging and create the Bottle application
logging.basicConfig(format="[%(levelname)s] lwr: %(message)s", level=logging.WARNING)


@click.group(
    epilog="For more information, see https://github.com/developerproductivity/logilica-weekly-report#logilica-weekly-report"
)
@click.option(
    "--username",
    "-u",
    envvar="LOGILICA_EMAIL",
    required=True,
    show_default=True,
    show_envvar=True,
    help="Logilica Login Credentials: User Email",
)
@click.password_option(
    "--password",
    "-p",
    envvar="LOGILICA_PASSWORD",
    show_default=True,
    show_envvar=True,
    required=True,
    help="Logilica Login Credentials: Password",
)
@click.option(
    "--domain",
    "-d",
    envvar="LOGILICA_DOMAIN",
    show_default=True,
    show_envvar=True,
    required=True,
    help="Logilica Login Credentials: Organization Name",
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
    domain: str,
    username: str,
    password: str,
    pwdebug: bool,
    verbose: int,
) -> None:
    """A tool to automate UI interactions with Logilica.

    \f

    The main command group for `Logilica UI` automation tool.

    Using the Click support, we parse the command line, extract the
    configuration information, store some of it in the Click context, and then
    pass it to other commands that interact with UI using Playwright.
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
            validate(instance=configuration, schema=schema)
            logging.debug("configuration: %s", str(configuration))
        except ValidationError as e:
            logging.error("configuration: %s", str(configuration))
            click.echo(f"Invalid YAML configuration: {e}", err=True)
            context.exit(5)

    """Main command group to handle common parameters"""
    context.ensure_object(dict)
    context.obj["configuration"] = configuration
    context.obj["logilica_credentials"] = {
        "username": username,
        "password": password,
        "domain": domain,
    }


for command in [weekly_report, data_sources]:
    cli.add_command(command)

if __name__ == "__main__":
    cli()
