from StringIO import StringIO

from mock import MagicMock
from mock import patch
from pytest import raises

from paasta_tools.paasta_cli.cmds.generate_pipeline import paasta_generate_pipeline
from paasta_tools.paasta_cli.cmds.generate_pipeline import generate_pipeline
from paasta_tools.paasta_cli.utils import NoSuchService


@patch('paasta_tools.paasta_cli.cmds.generate_pipeline.validate_service_name', autospec=True)
@patch('paasta_tools.paasta_cli.cmds.generate_pipeline.guess_service_name', autospec=True)
@patch('sys.stdout', new_callable=StringIO)
def test_paasta_generate_pipeline_service_not_found(
        mock_stdout, mock_guess_service_name, mock_validate_service_name):
    # paasta generate cannot guess service name and none is provided

    mock_guess_service_name.return_value = 'not_a_service'
    mock_validate_service_name.side_effect = NoSuchService(None)

    args = MagicMock()
    args.service = None
    expected_output = "%s\n" % NoSuchService.GUESS_ERROR_MSG

    # Fail if exit(1) does not get called
    with raises(SystemExit) as sys_exit:
        paasta_generate_pipeline(args)

    output = mock_stdout.getvalue()
    assert sys_exit.value.code == 1
    assert output == expected_output


@patch('paasta_tools.paasta_cli.cmds.generate_pipeline._run', autospec=True)
def test_generate_pipeline_run_fails(
        mock_run
):
    mock_run.return_value = (1, 'Big bad wolf')
    with raises(SystemExit) as sys_exit:
        generate_pipeline('fake_service')
    assert sys_exit.value.code == 1


@patch('paasta_tools.paasta_cli.cmds.generate_pipeline._run', autospec=True)
def test_generate_pipeline_success(
        mock_run,
):
    mock_run.return_value = (0, 'Everything OK')
    assert generate_pipeline('fake_service') is None


@patch('paasta_tools.paasta_cli.cmds.generate_pipeline._run', autospec=True)
@patch('paasta_tools.paasta_cli.cmds.generate_pipeline.get_team_email_address', autospec=True)
def test_generate_pipeline_calls_the_right_commands_and_owner(
        mock_get_team_email_address,
        mock_run,
):
    mock_run.return_value = (0, 'Everything OK')
    mock_get_team_email_address.return_value = 'fake_email'
    generate_pipeline('fake_service')
    assert mock_run.call_count == 2
    expected_cmd1 = 'fab_repo setup_jenkins:services/fake_service,profile=paasta_boilerplate,owner=fake_email'
    mock_run.assert_any_call(expected_cmd1, timeout=90)
    expected_cmd2 = 'fab_repo setup_jenkins:services/fake_service,profile=paasta,job_disabled=False,owner=fake_email'
    mock_run.assert_any_call(expected_cmd2, timeout=90)


@patch('paasta_tools.paasta_cli.cmds.generate_pipeline._run', autospec=True)
@patch('paasta_tools.paasta_cli.cmds.generate_pipeline.get_team_email_address', autospec=True)
@patch('paasta_tools.paasta_cli.cmds.generate_pipeline.get_team', autospec=True)
def test_generate_pipeline_uses_team_name_as_fallback_for_owner(
        mock_get_team,
        mock_get_team_email_address,
        mock_run,
):
    mock_run.return_value = (0, 'Everything OK')
    mock_get_team_email_address.return_value = None
    mock_get_team.return_value = "fake_team"
    generate_pipeline('fake_service')
    assert mock_run.call_count == 2
    expected_cmd1 = 'fab_repo setup_jenkins:services/fake_service,profile=paasta_boilerplate,owner=fake_team'
    mock_run.assert_any_call(expected_cmd1, timeout=90)
    expected_cmd2 = 'fab_repo setup_jenkins:services/fake_service,profile=paasta,job_disabled=False,owner=fake_team'
    mock_run.assert_any_call(expected_cmd2, timeout=90)


@patch('paasta_tools.paasta_cli.cmds.generate_pipeline.validate_service_name', autospec=True)
@patch('paasta_tools.paasta_cli.cmds.generate_pipeline.guess_service_name', autospec=True)
@patch('paasta_tools.paasta_cli.cmds.generate_pipeline.generate_pipeline', autospec=True)
def test_paasta_generate_pipeline_success_no_opts(
        mock_generate_pipeline,
        mock_guess_service_name,
        mock_validate_service_name):
    # paasta generate succeeds when service name must be guessed
    mock_guess_service_name.return_value = 'fake_service'
    mock_validate_service_name.return_value = None
    args = MagicMock()
    args.service = None
    assert paasta_generate_pipeline(args) is None
    mock_generate_pipeline.assert_called_once_with(service='fake_service')


@patch('paasta_tools.paasta_cli.cmds.generate_pipeline.validate_service_name', autospec=True)
@patch('paasta_tools.paasta_cli.cmds.generate_pipeline.generate_pipeline', autospec=True)
def test_generate_pipeline_success_with_opts(
        mock_generate_pipeline,
        mock_validate_service_name):
    # paasta generate succeeds when service name provided as arg
    mock_validate_service_name.return_value = None
    args = MagicMock()
    args.service = 'fake_service'
    assert paasta_generate_pipeline(args) is None
    mock_generate_pipeline.assert_called_once_with(service='fake_service')
