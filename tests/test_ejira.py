import os

import pytest

from gjira import gjira, git


def test_issue_attr(jira_issue, jira_attributes):
    result = {}
    for attr in jira_attributes:
        result[attr] = gjira.issue_attr(jira_issue, attr)
    assert result == {
        "issuetype": "ISSUE TYPES",
        "key": "ISSUE KEY",
        "parent.key": "PARENT KEY",
        "parent.summary": "PARENT SUMMARY",
        "summary": "ISSUE SUMMARY",
        "votes.votes": "ISSUE VOTES 4",
    }


def test_issue_attr_with_invalid_missing_attrs(jira_issue, jira_attributes):
    mocker.patch.object("jira.Issue", "fields", None)
    # delattr(getattr(jira_issue, "fields"), "votes")

    result = {}
    for attr in jira_attributes:
        result[attr] = gjira.issue_attr(jira_issue, attr)
    assert result == {
        "issuetype": "ISSUE TYPES",
        "key": "ISSUE KEY",
        "parent.key": "PARENT KEY",
        "parent.summary": "PARENT SUMMARY",
        "summary": "ISSUE SUMMARY",
        "votes.votes": None,
    }


def test_get_issue(jira_connection, jira_issue, jira_attributes):
    setattr(jira_connection, "issue", lambda id, fields: jira_issue)
    result = gjira.get_issue(jira_connection, "JIRA_ID", jira_attributes)

    assert result == {
        "issuetype": "ISSUE TYPES",
        "key": "ISSUE KEY",
        "parent__key": "PARENT KEY",
        "parent__summary": "PARENT SUMMARY",
        "summary": "ISSUE SUMMARY",
        "votes__votes": "ISSUE VOTES 4",
    }


def test_get_issue_with_invalid_attr(jira_connection, jira_issue, jira_attributes):
    delattr(getattr(jira_issue, "fields"), "votes")
    setattr(jira_connection, "issue", lambda id, fields: jira_issue)
    result = gjira.get_issue(jira_connection, "JIRA_ID", jira_attributes)

    assert result == {
        "issuetype": "ISSUE TYPES",
        "key": "ISSUE KEY",
        "parent__key": "PARENT KEY",
        "parent__summary": "PARENT SUMMARY",
        "summary": "ISSUE SUMMARY",
        "votes__votes": None,
    }


def test_issue_attr_with_invalid_missing_attrs(jira_issue, jira_attributes):
    delattr(getattr(jira_issue, "fields"), "votes")

    result = {}
    for attr in jira_attributes:
        result[attr] = gjira.issue_attr(jira_issue, attr)
    assert result == {
        "issuetype": "ISSUE TYPES",
        "key": "ISSUE KEY",
        "parent.key": "PARENT KEY",
        "parent.summary": "PARENT SUMMARY",
        "summary": "ISSUE SUMMARY",
        "votes.votes": None,
    }


def test_get_jira_config(mocker):
    environ_mock = mocker.patch.dict(
        os.environ,
        {
            "jiraserver": "http://testserver.com",
            "jirauser": "test-user@test.com",
            "jiratoken": "172y1dsyd7asda",
        },
    )
    assert gjira.get_jira_from_env() == {
        "server": "http://testserver.com",
        "basic_auth": (
            "test-user@test.com",
            "172y1dsyd7asda",
        ),
    }


def test_update_commit_msg_without_summary(mocker):
    file_text = """
    # A properly formed Git commit subject line should always be able to complete
    # the following sentence:
    #     * If applied, this commit <will your subject line here>
    #
    # [Add/Fix/Remove/Update/Refactor/Document/Style]: [issue #id] [summary]
    """

    fmt = "Jira issue: {ID-123}\nJira story {ID-456}"

    open_mock = mocker.patch("builtins.open", mocker.mock_open(read_data=file_text))

    gjira.update_commit_message("testfile", fmt)
    open_mock.assert_called_once_with("testfile", "r+")
    write = open_mock()

    assert f"\nJira information:\n{fmt}\n\n" == write.write.call_args_list[-1].args[0]
    for (line, call) in zip(file_text.split("\n"), write.write.call_args_list[:6]):
        assert line.strip() in call.args[0].strip("\n")


def test_update_commit_msg_with_summary(mocker):
    file_text = """This is a summary and jira should be added in the next line after the comment."""

    fmt = "Jira issue: {ID-123}\nJira story {ID-456}"
    open_mock = mocker.patch("builtins.open", mocker.mock_open(read_data=file_text))

    gjira.update_commit_message("testfile", fmt)
    open_mock.assert_called_once_with("testfile", "r+")
    write = open_mock()

    assert f"\nJira information:\n{fmt}\n\n" == write.write.call_args_list[-1].args[0]
    for (line, call) in zip(file_text.split("\n"), write.write.call_args_list[:6]):
        assert line.strip() in call.args[0].strip("\n")


def test_update_commit_msg_with_empty_text(mocker):
    file_text = ""
    fmt = "Jira issue: 123\nJira story: 1234"

    open_mock = mocker.patch("builtins.open", mocker.mock_open(read_data=file_text))

    gjira.update_commit_message("testfile", fmt)
    open_mock.assert_called_once_with("testfile", "r+")
    write = open_mock()

    assert f"\nJira information:\n{fmt}\n\n" == write.write.call_args_list[0].args[0]
    for (line, call) in zip(file_text.split("\n")[1:], write.write.call_args_list[2:]):
        assert line.strip() in call.args[0].strip("\n")


def test_update_commit_msg_with_empty_text(mocker):
    file_text = ""
    fmt = "Jira issue: 123\nJira story: 1234"

    open_mock = mocker.patch("builtins.open", mocker.mock_open(read_data=file_text))

    gjira.update_commit_message("testfile", fmt)
    open_mock.assert_called_once_with("testfile", "r+")
    write = open_mock()

    assert f"\nJira information:\n{fmt}\n\n" == write.write.call_args_list[0].args[0]
    for (line, call) in zip(file_text.split("\n")[1:], write.write.call_args_list[2:]):
        assert line.strip() in call.args[0].strip("\n")


def test_get_issue_raises_exception_and_return_empty_dict(mocker, jira_connection):
    requests_get_mock = mocker.patch("requests.sessions.Session.get")
    requests_get_mock.return_value.status_code = 404
    requests_get_mock.return_value.text = {}

    result = gjira.get_issue(jira_connection, "JIRA_ID", ("a, b"))
    assert result == {}


def test_is_jira_in_file(mocker):
    file_text = f"""
    # A properly formed Git commit subject line should always be able to complete
    # the following sentence:
    #     * If applied, this commit <will your subject line here>
    #
    # [Add/Fix/Remove/Update/Refactor/Document/Style]: [issue #id] [summary]

    {gjira.GJIRA_START_TEXT}\n:
    Issue: ..
    """

    open_mock = mocker.patch("builtins.open", mocker.mock_open(read_data=file_text))

    result = gjira.is_gjira_in_file("file_text_path")
    open_mock.assert_called_once_with("file_text_path")
    assert result == True


def test_is_jira_in_file(mocker):
    file_text = f"""
    # A properly formed Git commit subject line should always be able to complete
    # the following sentence:
    #     * If applied, this commit <will your subject line here>
    #
    # [Add/Fix/Remove/Update/Refactor/Document/Style]: [issue #id] [summary]

    Issue: ..
    """

    open_mock = mocker.patch("builtins.open", mocker.mock_open(read_data=file_text))

    result = gjira.is_gjira_in_file("file_text_path")
    open_mock.assert_called_once_with("file_text_path")
    assert result == False
