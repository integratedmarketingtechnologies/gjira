#!/usr/bin/env python3

import io
import os
import pathlib
import subprocess
import sys
from typing import Iterable

from jira import JIRA
from jira.exceptions import JIRAError

GJIRA_START_TEXT = "Jira information:"

GIT_START_LINES = "# Please enter the commit message for your changes. Lines starting\n"


def get_branch_name() -> str:
    return subprocess.check_output(("git", "rev-parse", "--abbrev-ref", "HEAD")).decode(
        "UTF-8"
    )


def get_jira_from_env() -> dict:
    return {
        "server": os.environ.get("jiraserver"),
        "basic_auth": (os.environ.get("jirauser"), os.environ.get("jiratoken")),
    }


def get_issue(jira: JIRA, id: str, attributes: Iterable) -> dict:
    try:
        issue = jira.issue(id, fields=", ".join(attributes))
        return {k: v for (k, v) in ((i, getattr(issue, i, None)) for i in attributes)}
    except JIRAError as e:
        if e.status_code == 404:
            print(f"Issue '{id}' not found.")
        else:
            print(
                f"Error fetching issue '{id}'. Status code: {e.status_code} | {e.msg}"
            )
        return {}


def is_gjira_in_file(path: str) -> bool:
    with open(path) as fd:
        for line in fd:
            if line.strip() == GJIRA_START_TEXT:
                return True
        return False


def update_commit_message(filename: str, content: str) -> list:
    if not content:
        return

    with open(filename, "r+") as fd:
        pos = 0
        lines = []
        for i, line in enumerate(fd):
            lines.append(line)
            # have we found where git default msg starts?
            if line == GIT_START_LINES:
                pos = i  # line number of git's default message
                break

        content = f"{GJIRA_START_TEXT}\n{content}\n"
        if len(lines) > 1:
            if lines[pos - 1 if pos else 0].count("\n") > 1:
                content = f"{content}\n"
            else:
                content = f"\n{content}\n"
        else:
            content = f"\n{content}\n"

        # add fmt to the corresponding position and read any unread line
        lines = lines[:pos] + [content] + lines[pos:] + fd.readlines()

        # Write lines back to file
        fd.seek(0)
        for line in lines:
            fd.write(line)

        return lines
