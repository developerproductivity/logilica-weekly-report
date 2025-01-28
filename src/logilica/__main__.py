import logging
import os
import pathlib

import click
import yaml

from jsonschema import validate, ValidationError

from logilica.configuration_schema import schema
from logilica.data_sources import data_sources
from logilica.weekly_report import weekly_report

# Default values for command options
DEFAULT_CONFIG_FILE = "./logilica.yaml"

# Set up logging and create the Bottle application
logging.basicConfig(format="[%(levelname)s] l-a: %(message)s", level=logging.WARNING)


@click.group()
@click.option(
    "--username",
    "-u",
    envvar="LOGILICA_EMAIL",
    required=True,
    help="Logilica User Email. You can also pass it using LOGILICA_EMAIL env variable.",
)
@click.option(
    "--password",
    "-p",
    envvar="LOGILICA_PASSWORD",
    required=True,
    help="Logilica User Password. You can also pass it using LOGILICA_EMAIL env variable.",
)
@click.option(
    "--domain",
    "-d",
    envvar="LOGILICA_DOMAIN",
    required=True,
    help="Logilica Domain. You can also pass it using LOGILICA_EMAIL env variable.",
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

    The main function for the `logilica` tool

    Using the Click support, we parse the command line, extract the
    configuration information, store some of it in the Click context, and then
    pass it to other commands
    """

    if verbose:
        logging.getLogger().setLevel(logging.INFO if verbose == 1 else logging.DEBUG)
        logging.debug("Debug mode enabled")

    if pwdebug:
        # Playwright debug mode requested:  enable Playwright debug support.
        os.environ["PWDEBUG"] = "1"
        logging.debug("Playwright debug mode enabled")

    """
    if not domain:
        click.echo(f"Logilica domain was not provided", err=True)
        context.exit(2)
    if not username:
        click.echo(f"Logilica username was not provided", err=True)
        context.exit(2)
    if not password:
        click.echo(f"Logilica password was not provided", err=True)
        context.exit(2)
    """
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
    context.obj["verbose"] = verbose
    context.obj["pwdebug"] = pwdebug
    context.obj["configuration"] = configuration
    context.obj["credentials"] = {
        "username": username,
        "password": password,
        "domain": domain,
    }


for command in [data_sources, weekly_report]:
    cli.add_command(command)

if __name__ == "__main__":
    cli()
