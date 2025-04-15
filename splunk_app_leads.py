#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.12"
# dependencies = [
# "requests","click"
# ]
# ///

"""terribly janky script to make things go"""

from datetime import datetime
import os
import sys
from typing import Optional
import click
import requests


def get_app_leads(token: str, app_id: int) -> None:
    cookies = {
        "splunkbase_cookie_policy_accepted": "true",
    }

    headers = {
        "Authorization": f"Bearer {token}",
    }

    response = requests.get(
        f"https://classic.splunkbase.splunk.com/api/v1/app/{app_id}/leads",
        cookies=cookies,
        headers=headers,
        allow_redirects=True,
    )
    try:
        response.raise_for_status()
        print(response.text)
    except Exception as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        print("Response status code:", response.status_code, file=sys.stderr)
        if "Log Into Your Splunk Account" in str(response.text):
            print("Got the login page!", file=sys.stderr)
        else:
            print(f"Response text:\n{response.text}", file=sys.stderr)


def auth(username: str, password: str) -> Optional[str]:
    url = "https://api.splunk.com/2.0/rest/login/splunk"

    response = requests.get(
        url,
        allow_redirects=False,
        auth=(username, password),
    )
    try:
        # print(response.json())
        if response.status_code == 200:
            print("Auth successful", file=sys.stderr)
            return response.json().get("data", {}).get("token")
        else:
            print("Auth failed", file=sys.stderr)
            return None
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        print("Response status code:", response.status_code)


def check_env_vars() -> None:
    """checks if there's any missing env vars for config"""
    missing_env = False
    for var in ["SPLUNK_USERNAME", "SPLUNK_PASSWORD"]:
        if os.environ.get(var) is None:
            missing_env = True
            print(f"Please set the {var} environment variable", file=sys.stderr)
    if missing_env:
        sys.exit(1)


@click.command()
@click.argument("start_date")
@click.argument("end_date")
@click.argument("splunk_app_id", type=int)
def main(start_date: str, end_date: str, splunk_app_id: int) -> None:
    try:
        start_date_parsed = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_parsed = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        print("Dates must be in YYYY-MM-DD format", file=sys.stderr)
        sys.exit(1)

    if start_date_parsed > end_date_parsed:
        print("Start date must be before end date", file=sys.stderr)
        sys.exit(1)

    check_env_vars()

    token = auth(os.environ["SPLUNK_USERNAME"], os.environ["SPLUNK_PASSWORD"])
    if token is None:
        print("Auth unsuccessful", file=sys.stderr)
        sys.exit(1)
    get_app_leads(token, splunk_app_id)


if __name__ == "__main__":
    main()
