# logilica-weekly-report

This project exports charts and text from Logilica reports and (will eventually)
add the content to a Google Doc such as a weekly report.

The tool is configured via a YAML file which contains configuration options as
well as a list of teams.  For each team, it specifies a list of Logilica
dashboards and the team's Jira project.  For each dashboard, it specifies the
name of an output file (which must not conflict with any other team's dashboards'
output files) and possibly other attributes.  By default, the file
`weekly_report.yaml` in the current directory is used, but an alternate path can
be specified on the command line.

To onboard a new team, create a new Logilica dashboard for it and add the team
and the dashboard information to the configuration file.

Credentials for accessing Logilica are provided by the environment variables,
`LOGILICA_DOMAIN`, `LOGILICA_EMAIL`, and `LOGILICA_PASSWORD`.  (Note to the
Developer Practices Team:  the appropriate values for the bot account can be
obtained from the Bitwarden vault.)

To run the script, check out the Git repo and run:  ```pip install -r requirements.txt .```
We recommend doing this inside a [virtual environment](https://docs.python.org/3/library/venv.html).
(If you are doing development on the tool, you may want to specify `-e` in the
`pip install` command.)  After installing the tool, you also need to install
the browser which it uses to interact with the Logilica web UI:
```playwright install chromium```  (For details on debugging the web interactions,
see the `--pwdebug` option in the command help, below, and the
[Playwright documentation](https://playwright.dev/python/docs/running-tests).)

The PDF files containing the downloaded Logilica reports are stored in a
temporary directory which is created if it does not exist; if it was created by
the tool, the directory is deleted after execution is complete.  By default,
the directory is named `lwr_downloaded_pdfs`, and it is created in the current
directory, but an alternate path can be specified on the command line.

Help is available on the command line:
```text
$ logilica-weekly-report --help
Usage: logilica-weekly-report [OPTIONS]

  A tool for fetching Logilica reports, extracting their contents, and adding
  them to a Google Doc.

Options:
  -C, --config FILE          Path to configuration file  [default:
                             ./weekly_report.yaml]
  -d, --downloads DIRECTORY  Path to a directory to receive downloaded
                             files (will be created if it doesn't exist; will
                             be deleted if created)  [default:
                             ./lwr_downloaded_pdfs]
  -D, --pwdebug, --PWD       Enable Playwright debug mode
  -v, --verbose              Enable verbose mode; specify multiple times to
                             increase verbosity
  --help                     Show this message and exit.

  For more information, see https://github.com/developerproductivity/logilica-
  weekly-report#logilica-weekly-report
```

Some dashboards can be quite slow to load into the UI, so, if you are running
the tool interactively and wish to track its progress, add a `-v` to the command
line to see informational messages.  (If you are debugging or just nosy, adding
a _second_ `-v` will add debugging messages to the output.)
