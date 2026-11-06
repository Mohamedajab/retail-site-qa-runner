import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

from .expected import PRODUCT, SCENARIOS
from .evidence import sanitise_trace
from .fixture import shop
from .report import save_report


def run_scenario(browser, base, scenario, output, video=False):
    context = browser.new_context(
        viewport={"width": 1000, "height": 760},
        record_video_dir=str(output / "videos") if video else None,
    )
    context.tracing.start(screenshots=True, snapshots=True, sources=False)
    page = context.new_page()
    page.set_default_timeout(2500)
    errors, checks = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))

    def check(name, expected, observe, compare=None):
        started = time.perf_counter()
        record = {
            "id": f"{scenario}/{name}",
            "scenario": scenario,
            "expected": expected,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        try:
            observed = observe()
            record.update(
                observed=observed,
                status="PASS"
                if (compare(observed) if compare else observed == expected)
                else "FAIL",
            )
        except Exception as error:
            record.update(observed=type(error).__name__, status="ERROR")
        record["duration_ms"] = round((time.perf_counter() - started) * 1000, 2)
        checks.append(record)

    try:
        page.goto(f"{base}/{scenario}/", wait_until="networkidle")
        response = context.request.get(f"{base}/{scenario}/api/product")
        try:
            data = response.json()
        except (ValueError, json.JSONDecodeError):
            data = None
        check(
            "api",
            PRODUCT,
            lambda: (
                data if response.status == 200 else {"http_status": response.status}
            ),
        )
        check("title", PRODUCT["title"], lambda: page.locator("#title").inner_text())
        if not isinstance(data, dict) or "price" not in data:
            check("price", PRODUCT["price"], lambda: "API dependency unavailable")
            checks[-1]["status"] = "UNAVAILABLE"
        else:
            check(
                "price",
                {"page": PRODUCT["price"], "api": PRODUCT["price"]},
                lambda: {
                    "page": page.locator("#price").inner_text(),
                    "api": data["price"],
                },
            )
        check("stock", PRODUCT["stock"], lambda: page.locator("#stock").inner_text())
        check(
            "image",
            True,
            lambda: page.locator("img").evaluate(
                "img => img.complete && img.naturalWidth > 0"
            ),
        )

        def basket():
            page.get_by_role("button", name="Add to basket").click()
            return page.locator("#basket").inner_text()

        check("basket", "1", basket)
        check("javascript", [], lambda: errors.copy())
        page.screenshot(path=str(output / f"{scenario}.png"), full_page=True)
    except Exception as error:
        checks.append(
            {
                "id": f"{scenario}/execution",
                "scenario": scenario,
                "expected": "Fixture and browser available",
                "observed": type(error).__name__,
                "status": "ERROR",
                "timestamp": datetime.now(UTC).isoformat(),
                "duration_ms": 0,
            }
        )
    finally:
        context.tracing.stop(path=str(output / f"{scenario}.zip"))
        sanitise_trace(output / f"{scenario}.zip")
        context.close()
    return checks


def main():
    parser = argparse.ArgumentParser(
        description="Check the local demo shop and save a report"
    )
    parser.add_argument("--scenario", choices=(*SCENARIOS, "all"), default="healthy")
    parser.add_argument("--output", type=Path, default=Path("artifacts"))
    parser.add_argument("--record-video", action="store_true")
    parser.add_argument("--ai", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    checks = []
    try:
        with shop() as base, sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            for scenario in SCENARIOS if args.scenario == "all" else [args.scenario]:
                checks.extend(
                    run_scenario(
                        browser, base, scenario, args.output, args.record_video
                    )
                )
            browser.close()
    except Exception as error:
        checks.append(
            {
                "id": "runner/execution",
                "scenario": "runner",
                "expected": "Configured browser",
                "observed": type(error).__name__,
                "status": "ERROR",
                "timestamp": datetime.now(UTC).isoformat(),
                "duration_ms": 0,
            }
        )
    ai = {"status": "disabled"}
    if args.ai:
        from .triage import triage

        ai = triage(checks, Path.home() / ".retail-qa-budget.db")
    report = save_report(args.output, checks, ai)
    print(
        f"{len(checks)} checks; exit {report['exit_code']}; {args.output / 'report.html'}"
    )
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
