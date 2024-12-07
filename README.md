# logilica-weekly-report

This project exports Logilica data to add it to a weekly report. 

The list of teams is read from the local `weekly_report.yaml` file.

When a new team is onboarded, a new dashboard should be created for it, and the 
`weekly_report.yaml` file is updated accordingly.

Environment variables must be set for `LOGILICA_DOMAIN`, `LOGILICA_EMAIL`, and
`LOGILICA_PASSWORD`, the corresponding values can be obtained from Bitwarden.

To run the script checkout the git repo and to setup your environment run 
`pip install -r src/requirements.txt` 

To run in debug mode:
`PWDEBUG=1 python3 download_pdfs.py`. For mode details on running and debugging 
see https://playwright.dev/python/docs/running-tests.

The downloaded PDF files will be stored in the location defined by `Download_path:` in the `weekly_report.yaml` file.

