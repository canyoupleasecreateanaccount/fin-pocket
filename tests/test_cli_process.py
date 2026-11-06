"""Check process exit status for both public CLI entry points without network."""

import subprocess
import sys
import textwrap

import pytest


@pytest.mark.parametrize("entry_point", ["console", "module"])
@pytest.mark.parametrize("outcome", ["ConnectionError", "ValueError", "success"])
def test_cli_process(entry_point, outcome):
    result = subprocess.run(
        [sys.executable, "-c", textwrap.dedent("""\
            import runpy
            import sys
            from pathlib import Path
            from unittest.mock import MagicMock, patch

            entry_point, outcome = sys.argv[1:]
            sys.argv = ["fin-pocket", "TEST"]
            data = MagicMock()
            data.__len__.return_value = 2
            data.index = ["2024-01-02", "2024-01-03"]
            with patch("fin_pocket.cli.DataProvider") as provider, \\
                 patch("fin_pocket.cli.Chart"):
                if outcome == "success":
                    provider.return_value.fetch.return_value = data
                else:
                    error = {"ConnectionError": ConnectionError, "ValueError": ValueError}[outcome]
                    provider.return_value.fetch.side_effect = error("simulated")
                if entry_point == "console":
                    runpy.run_path(str(Path(sys.executable).with_name("fin-pocket")), run_name="__main__")
                else:
                    runpy.run_module("fin_pocket", run_name="__main__")
            """), entry_point, outcome],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if outcome == "success":
        assert result.returncode == 0, result.stderr
        assert "Loaded 2 records for TEST (daily)" in result.stdout
        assert result.stderr == ""
    else:
        assert result.returncode != 0
        assert result.stdout == ""
        assert result.stderr == "Error: simulated\n"
