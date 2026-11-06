import html
import json
import sqlite3
import uuid
from pathlib import Path


def exit_code(checks):
    if any(c["status"] == "ERROR" for c in checks):
        return 2
    return int(any(c["status"] == "FAIL" for c in checks))


def save_report(output, checks, ai):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    report = {
        "run_id": uuid.uuid4().hex,
        "exit_code": exit_code(checks),
        "checks": checks,
        "ai": ai,
    }
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    def esc(value):
        return html.escape(str(value))

    rows = ""
    for c in checks:
        links = " · ".join(
            f'<a href="{esc(c["scenario"])}.{extension}">{label}</a>'
            for extension, label in (("png", "Screenshot"), ("zip", "Trace"))
            if (output / f"{c['scenario']}.{extension}").exists()
        )
        rows += f'<tr><td>{esc(c["scenario"])}</td><td>{esc(c["id"])}</td><td class="{c["status"]}">{c["status"]}</td><td>{esc(c["expected"])}</td><td>{esc(c["observed"])}</td><td>{esc(c["timestamp"])}</td><td>{c["duration_ms"]}</td><td>{links}</td></tr>'
    (output / "report.html").write_text(
        """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Retail QA results</title><style>body{font:16px system-ui;margin:24px;color:#17333d}section{overflow:auto}table{border-collapse:collapse;min-width:1000px}td,th{border:1px solid #aaa;padding:10px;text-align:left}.PASS{color:#17612b}.FAIL{color:#ae1625}.ERROR{color:#805400}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><h1>Retail QA results</h1><p>Local demo shop. PASS = assertion met; FAIL = observed regression; ERROR = execution failure; UNAVAILABLE = check blocked by a failed dependency. Model suggestions cannot change these results.</p><section><table><thead><tr><th>Scenario</th><th>Check ID</th><th>Result</th><th>Expected</th><th>Observed</th><th>UTC timestamp</th><th>ms</th><th>Files</th></tr></thead><tbody>"""
        + rows
        + "</tbody></table></section><h2>Model suggestions — check before use</h2><pre>"
        + esc(json.dumps(ai, indent=2))
        + "</pre></html>",
        encoding="utf-8",
    )
    with sqlite3.connect(output / "history.db") as db:
        db.execute("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, report TEXT)")
        db.execute(
            "INSERT INTO runs VALUES (?, ?)", (report["run_id"], json.dumps(report))
        )
        db.execute(
            "DELETE FROM runs WHERE rowid NOT IN (SELECT rowid FROM runs ORDER BY rowid DESC LIMIT 20)"
        )
    return report
