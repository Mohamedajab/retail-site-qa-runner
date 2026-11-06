"""Run six demo cases. Paid requests require --ai."""

import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from retail_qa.expected import DEFECTS, SCENARIOS
from retail_qa.fixture import shop
from retail_qa.report import save_report
from retail_qa.runner import run_scenario
from retail_qa.triage import triage


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ai", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("artifacts/evaluation"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results, all_checks = [], []
    with shop() as base, sync_playwright() as pw:
        browser = pw.chromium.launch()
        for scenario in SCENARIOS[:6]:
            checks = run_scenario(browser, base, scenario, args.output)
            ai = (
                triage(checks, Path.home() / ".retail-qa-budget.db")
                if args.ai
                else {"status": "disabled"}
            )
            expected_ids = (
                {f"{scenario}/{DEFECTS[scenario]}"} if scenario in DEFECTS else set()
            )
            referenced = {
                i
                for f in ai.get("output", {}).get("findings", [])
                for i in f["check_ids"]
            }
            results.append(
                {
                    "scenario": scenario,
                    "expected_failed_ids": sorted(expected_ids),
                    "ai": ai,
                    "assessment": "References match the failed checks; review the suggestions before use"
                    if ai["status"] == "available" and referenced == expected_ids
                    else "unavailable or incomplete references",
                }
            )
            all_checks.extend(checks)
        # Recording shows real observed results, in order, without any provider credentials.
        context = browser.new_context(
            record_video_dir=str(args.output / "videos"),
            viewport={"width": 1000, "height": 760},
        )
        page = context.new_page()
        for scenario in ("healthy", "wrong-price", "repaired"):
            checks = run_scenario(browser, base, scenario, args.output)
            page.goto(f"{base}/{scenario}/")
            failures = [c["id"] for c in checks if c["status"] != "PASS"]
            page.evaluate(
                "text => {const p=document.createElement('p');p.textContent=text;p.style='background:#fff;padding:16px;border:2px solid';document.body.prepend(p)}",
                f"{scenario}: "
                + (", ".join(failures) if failures else "7 checks passed"),
            )
            page.wait_for_timeout(1800)
        video = page.video
        context.close()
        video.save_as(args.output / "healthy-broken-repaired.webm")
        video.delete()
        browser.close()
    (args.output / "evaluation.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    save_report(
        args.output,
        all_checks,
        {"label": "Model suggestions — check before use", "frozen_cases": results},
    )
    print(
        "Six cases recorded; see evaluation.json for actual availability, provider, usage and assessment."
    )


if __name__ == "__main__":
    main()
