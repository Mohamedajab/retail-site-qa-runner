# Retail Site QA Runner

A Python tool that checks a small demo shop in a browser. It checks product details,
prices, stock, images, the basket and JavaScript errors, then saves a report with
screenshots and traces. Everything runs locally. It does not test real shops.

![Demo shop](docs/example/healthy.png)

## Run it

Use Python 3.12 or newer.

```bash
python -m venv .venv
# Activate the environment. On Windows: .venv\Scripts\activate
pip install -e '.[dev]'
playwright install chromium
retail-qa
```

`retail-qa` starts the shop, runs the checks and stops the server. Results go into
`artifacts/`: an HTML report, JSON results, screenshots, browser traces and a SQLite
database holding the latest 20 runs.

```bash
retail-qa --scenario wrong-price   # A broken price: exit 1
retail-qa --scenario repaired      # Working shop: exit 0
retail-qa --scenario all           # All cases, including the five faults: exit 1
python scripts/evaluate.py         # Six test cases and a short recording; no paid calls
pytest -q
```

Exit codes: **0** for passing checks, **1** for a fault found in the shop and **2**
for a setup or execution problem. A check marked `UNAVAILABLE` could not run because
another check failed. For example, the tool cannot compare prices if the API sends
broken JSON. The other page checks still run.

Each case uses a fresh browser session. Expected values are kept separately in
[`expected.py`](retail_qa/expected.py), so a fault in the shop cannot change them.

| Test case | What should happen |
|---|---|
| healthy / repaired | All seven checks pass |
| wrong-price | Price check fails: the page shows £29 instead of £24 |
| missing-image | Image check fails: the image has not loaded |
| broken-basket | Basket check fails: clicking the button leaves the count at zero |
| malformed-api | API check fails; price comparison is unavailable |
| javascript-error | Error check fails: the page throws an exception |

Every result includes the expected value, what happened, the time and how long the
check took. To open a trace, run `playwright show-trace artifacts/wrong-price.zip`.

## Example results

- [HTML report](docs/example/report.html) — download and open it; GitHub shows the source.
- [JSON results](docs/example/report.json)
- [Working → broken → repaired recording](docs/example/healthy-broken-repaired.webm)
- [Six OpenRouter test results, including cost and responses](docs/example/evaluation.json)
- [Test notes](docs/verification.md)

## Optional OpenRouter summaries

Set `OPENROUTER_API_KEY` in your environment, then add `--ai` to a run:

```bash
retail-qa --scenario wrong-price --ai
```

This sends a small set of demo check results to `openai/gpt-4.1-mini` through
OpenRouter. It asks for a description of the problem and suggestions for where to
look. The report labels these as **Model suggestions — check before use**.
Suggestions must refer to checks that actually failed. They cannot change results,
run commands, edit files or fix the shop. If the request fails or the response is
invalid, the normal report is still saved. Requests use Python's standard library.

Before each request, the tool checks current prices and sets aside the maximum
possible cost in `~/.retail-qa-budget.db`. Limits are US$1 in total, ten requests,
12,000 bytes of check data and 500 output tokens per request. There are no automatic
retries. Failed or timed-out requests keep their reserved amount. Provider price
limits reject higher token prices and extra request fees. Keep the database to
preserve the spending limit; it does not limit other use of your account.

The six example cases are small tests of this feature. They do not show how well
the model would handle other websites or every attempt to mislead it.

## Tests and references

GitHub Actions runs the offline tests and browser checks separately, and uploads
the reports and traces. It makes no paid requests.

- [Playwright pytest guide](https://playwright.dev/python/docs/test-runners)
- [OpenRouter API](https://openrouter.ai/docs/api_reference/overview)
- [OWASP guidance on separating page data from model instructions](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)

The demo has one product and one basket action. Payments, accounts and production
monitoring are outside its scope.
