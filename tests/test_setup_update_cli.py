# tests/test_setup_update_cli.py
"""Lightweight parser tests for setup and update subcommands."""

from agentirc.cli import _build_parser


def test_setup_parser():
    """setup subcommand parses --config and --uninstall."""
    p = _build_parser()
    args = p.parse_args(["setup", "--uninstall"])
    assert args.command == "setup"
    assert args.uninstall is True

    args = p.parse_args(["setup", "--config", "/tmp/mesh.yaml"])
    assert args.config == "/tmp/mesh.yaml"


def test_update_parser():
    """update subcommand parses --dry-run, --skip-upgrade, --config."""
    p = _build_parser()
    args = p.parse_args(["update", "--dry-run", "--skip-upgrade"])
    assert args.command == "update"
    assert args.dry_run is True
    assert args.skip_upgrade is True

    args = p.parse_args(["update", "--config", "/tmp/mesh.yaml"])
    assert args.config == "/tmp/mesh.yaml"


def test_setup_in_dispatch():
    """setup command is wired into the dispatch table."""
    from agentirc import cli
    # The dispatch dict is built inside main(), so check the function exists
    assert hasattr(cli, "_cmd_setup")
    assert callable(cli._cmd_setup)


def test_update_in_dispatch():
    """update command is wired into the dispatch table."""
    from agentirc import cli
    assert hasattr(cli, "_cmd_update")
    assert callable(cli._cmd_update)
