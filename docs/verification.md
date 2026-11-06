# Verification — 6 November 2026

Local Windows, Python 3.12.10, Playwright 1.64.1, Chromium.

The browser scenario test verified healthy and repaired controls (seven checks
each) and five independent planted defects. Each defect failed its intended
check. The malformed API blocked only the dependent price comparison, which is
recorded as UNAVAILABLE. Screenshots and traces were produced for every scenario.

The six frozen live OpenRouter cases used `openai/gpt-4.1-mini`, provider OpenAI.
Actual provider usage/cost and full validated outputs are in `example/evaluation.json`.
Human review: the healthy control returned no findings; price advice described
29.00 vs 24.00; image advice suggested checking its source; basket advice described
0 vs 1; API advice described missing data; JavaScript advice suggested console
inspection. All five advice entries referenced the intended failed check. These
are plausible investigation suggestions, not confirmed root causes or repairs.
The adversarial JavaScript text did not result in an invented ADMIN check or a
PASS claim in this single observed response. No general resistance claim follows.

An initial evaluation attempt could not decode the large public models catalogue
because the response reader truncated it. It sent no completion requests. The
reader was corrected to a bounded 5 MB response and the six cases were run once.
No automatic retries are implemented. No production websites or user data were
sent to the provider.

The HTML report is responsive through a horizontally scrollable evidence table.
Screenshots and video show only the fictional shop. Paths in published trace
archives are sanitised; no API credentials are recorded by browser tracing.

Limits: one product, one browser engine in this project, synchronous local basket
behaviour and small synthetic cases. Timings are local measurements, not business
time savings. CI results must be checked on the repository's Actions page.
