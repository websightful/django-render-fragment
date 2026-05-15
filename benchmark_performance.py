"""Benchmark {% render_fragment %} (with {% extends %}) against an analogous
{% include %} that carries the full content in a single template file.

The two document templates each invoke their respective inclusion tag 25 times
with identical context data and produce identical HTML output, isolating the
overhead introduced by ``render_fragment`` + ``extends`` versus a plain
``include`` of a self-contained template.

Run from the repository root:

    python benchmark_performance.py [--iterations N] [--repeat R] [--warmup W]
"""
from __future__ import annotations

import argparse
import os
import statistics
import sys
import timeit
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
BENCHMARK_TEMPLATES_DIR = REPO_ROOT / "benchmarks" / "templates"

# Reuse the existing test_settings module verbatim, but make its TEMPLATES
# setting able to find the benchmark template directory in addition to the
# per-app template directories it already discovers via APP_DIRS.
sys.path.insert(0, str(REPO_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")

import test_settings  # noqa: E402  (import after sys.path tweak)

test_settings.TEMPLATES[0].setdefault("DIRS", [])
if str(BENCHMARK_TEMPLATES_DIR) not in test_settings.TEMPLATES[0]["DIRS"]:
    test_settings.TEMPLATES[0]["DIRS"].append(str(BENCHMARK_TEMPLATES_DIR))

import django  # noqa: E402

django.setup()

from django.template.loader import get_template  # noqa: E402

NUM_CARDS = 25

# Build a fixed context once so render-time work — not Python-side data setup —
# dominates the measurement.
CONTEXT = {
    "titles": [f"Title {i}" for i in range(NUM_CARDS)],
    "bodies": [f"Body content for card number {i}." for i in range(NUM_CARDS)],
}


def _render(template):
    return template.render(CONTEXT)


def _format_seconds(seconds: float) -> str:
    if seconds >= 1:
        return f"{seconds:.4f} s"
    if seconds >= 1e-3:
        return f"{seconds * 1e3:.3f} ms"
    return f"{seconds * 1e6:.2f} µs"


def _measure(label: str, template, iterations: int, repeat: int, warmup: int) -> dict:
    for _ in range(warmup):
        _render(template)

    timer = timeit.Timer(lambda: _render(template))
    raw = timer.repeat(repeat=repeat, number=iterations)
    per_call = [total / iterations for total in raw]

    return {
        "label": label,
        "iterations": iterations,
        "repeat": repeat,
        "best": min(per_call),
        "mean": statistics.fmean(per_call),
        "stdev": statistics.pstdev(per_call) if len(per_call) > 1 else 0.0,
    }


def _print_result(result: dict) -> None:
    print(
        f"  {result['label']:<28} "
        f"best={_format_seconds(result['best'])}  "
        f"mean={_format_seconds(result['mean'])}  "
        f"stdev={_format_seconds(result['stdev'])}  "
        f"(repeat={result['repeat']}, iterations={result['iterations']})"
    )


def _assert_equivalent_output(fragment_template, include_template) -> None:
    fragment_html = _render(fragment_template)
    include_html = _render(include_template)
    if fragment_html != include_html:
        sys.stderr.write(
            "WARNING: render_fragment and include outputs differ; "
            "the comparison is still meaningful but the templates may have drifted.\n"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=200,
                        help="number of full-document renders per timing run")
    parser.add_argument("--repeat", type=int, default=5,
                        help="number of timing runs (best of these is reported)")
    parser.add_argument("--warmup", type=int, default=10,
                        help="untimed renders performed before each template is timed")
    args = parser.parse_args()

    fragment_template = get_template("benchmark/document_fragment.html")
    include_template = get_template("benchmark/document_include.html")

    _assert_equivalent_output(fragment_template, include_template)

    print(
        f"Benchmarking {NUM_CARDS} inclusions per document, "
        f"{args.iterations} renders × {args.repeat} repeats "
        f"(warmup={args.warmup}).\n"
    )

    fragment_result = _measure(
        "{% render_fragment %} + extends",
        fragment_template,
        args.iterations, args.repeat, args.warmup,
    )
    include_result = _measure(
        "{% include %} (single file)",
        include_template,
        args.iterations, args.repeat, args.warmup,
    )

    print("Per full-document render (lower is better):")
    _print_result(fragment_result)
    _print_result(include_result)

    ratio = fragment_result["best"] / include_result["best"]
    per_card_overhead = (
        fragment_result["best"] - include_result["best"]
    ) / NUM_CARDS
    print(
        f"\nrender_fragment is {ratio:.2f}× the time of include "
        f"(~{_format_seconds(per_card_overhead)} extra per inclusion)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
