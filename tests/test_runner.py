import json
import os
import subprocess
import sys

import pytest
from retail_qa.expected import DEFECTS, SCENARIOS
from retail_qa.fixture import shop
from retail_qa.report import exit_code, save_report
from retail_qa.runner import run_scenario


def test_exit_codes_and_escaping(tmp_path):
    assert exit_code([{"status": "PASS"}]) == 0
    assert exit_code([{"status": "FAIL"}]) == 1
    assert exit_code([{"status": "FAIL"}, {"status": "ERROR"}]) == 2
    save_report(tmp_path, [], {"text": "<script>alert(1)</script>"})
    assert "<script>" not in (tmp_path / "report.html").read_text()
    assert json.loads((tmp_path / "report.json").read_text())["exit_code"] == 0


def test_configuration_failure_still_writes_report(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "retail_qa.runner",
            "--output",
            str(tmp_path / "report"),
        ],
        env={
            **os.environ,
            "PLAYWRIGHT_BROWSERS_PATH": str(tmp_path / "missing-browser"),
        },
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    report = json.loads((tmp_path / "report/report.json").read_text())
    assert report["checks"][0]["status"] == "ERROR"


@pytest.mark.browser
def test_independent_defects(browser, tmp_path):
    with shop() as base:
        for scenario in SCENARIOS:
            checks = run_scenario(browser, base, scenario, tmp_path)
            failed = {c["id"].split("/")[1] for c in checks if c["status"] == "FAIL"}
            assert failed == ({DEFECTS[scenario]} if scenario in DEFECTS else set())
            assert len(checks) == 7
            if scenario == "malformed-api":
                assert (
                    next(c for c in checks if c["id"].endswith("/price"))["status"]
                    == "UNAVAILABLE"
                )
            else:
                assert not any(c["status"] == "ERROR" for c in checks)
            assert (tmp_path / f"{scenario}.png").exists()
            assert (tmp_path / f"{scenario}.zip").exists()
