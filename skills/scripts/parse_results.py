#!/usr/bin/env python3
"""Parse OmniDocBench end2end result files and print a compact score report."""

import argparse
import json
from pathlib import Path


def get(data, path, default=None):
    cur = data
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def fmt(value, scale=1.0):
    if value is None:
        return "N/A"
    return f"{value * scale:.6f}"


def main():
    parser = argparse.ArgumentParser(description="Parse OmniDocBench metric/run summary files.")
    parser.add_argument("result_dir", help="Directory containing *_metric_result.json and related files")
    parser.add_argument("--prefix", help="Result prefix, e.g. mineru_quick_match. Auto-detected if omitted")
    parser.add_argument("--pred", help="Optional prediction markdown directory to count .md and empty .md files")
    args = parser.parse_args()

    result_dir = Path(args.result_dir)
    if args.prefix:
        prefix = args.prefix
    else:
        matches = sorted(result_dir.glob("*_metric_result.json"))
        if not matches:
            raise SystemExit(f"No *_metric_result.json found in {result_dir}")
        prefix = matches[0].name.removesuffix("_metric_result.json")

    metric_path = result_dir / f"{prefix}_metric_result.json"
    summary_path = result_dir / f"{prefix}_run_summary.json"
    stage_path = result_dir / f"{prefix}_stage_execution.json"
    runtime_path = result_dir / f"{prefix}_runtime_environment.json"

    with metric_path.open(encoding="utf-8") as f:
        metric = json.load(f)
    summary = json.load(summary_path.open(encoding="utf-8")) if summary_path.exists() else {}
    stage = json.load(stage_path.open(encoding="utf-8")) if stage_path.exists() else {}
    runtime = json.load(runtime_path.open(encoding="utf-8")) if runtime_path.exists() else {}

    scores = {
        "Overall": fmt(get(summary, ["notebook_metric_summary", "overall_notebook"])),
        "Text Edit Distance ↓": fmt(get(metric, ["text_block", "all", "Edit_dist", "ALL_page_avg"])),
        "Formula CDM ↑": fmt(get(metric, ["display_formula", "page", "CDM", "ALL"]), 100),
        "Formula Edit Distance ↓": fmt(get(metric, ["display_formula", "all", "Edit_dist", "ALL_page_avg"])),
        "Table TEDS ↑": fmt(get(metric, ["table", "page", "TEDS", "ALL"]), 100),
        "Table TEDS Structure Only ↑": fmt(get(metric, ["table", "page", "TEDS_structure_only", "ALL"]), 100),
        "Table Edit Distance ↓": fmt(get(metric, ["table", "all", "Edit_dist", "ALL_page_avg"])),
        "Reading Order Edit Distance ↓": fmt(get(metric, ["reading_order", "all", "Edit_dist", "ALL_page_avg"])),
    }

    print("## Result paths")
    print(f"- Output dir: `{result_dir}`")
    print(f"- Metric JSON: `{metric_path}`")
    if summary_path.exists():
        print(f"- Run summary: `{summary_path}`")
    print("\n## Scores")
    print("| Metric | Score |")
    print("|---|---:|")
    for name, value in scores.items():
        print(f"| {name} | **{value}** |")

    page_count = get(stage, ["page_match", "page_count"])
    quick_timeout = get(stage, ["page_match", "fallbacks", "quick_match_timeout", "count"])
    cdm = get(stage, ["metrics", "display_formula", "CDM"], {}) or {}
    teds = get(stage, ["metrics", "table", "TEDS"], {}) or {}
    texlive = get(runtime, ["texlive", "cjk_sty", "status"])
    magick = get(runtime, ["external_tools", "magick", "output"], "")
    gs = get(runtime, ["external_tools", "ghostscript", "output"])

    print("\n## Validation")
    if args.pred:
        pred_dir = Path(args.pred)
        if pred_dir.is_dir():
            md_files = list(pred_dir.glob("*.md"))
            empty_files = [path for path in md_files if path.stat().st_size == 0]
            print(f"- prediction md files: {len(md_files)}, empty: {len(empty_files)}")
            if 0 < len(empty_files) <= 10:
                print("- empty md files: " + ", ".join(path.name for path in sorted(empty_files)))
        else:
            print(f"- prediction md dir missing: {pred_dir}")
    if page_count is not None:
        print(f"- pages: {page_count}")
    if quick_timeout is not None:
        print(f"- quick_match_timeout_count: {quick_timeout}")
    if cdm:
        print("- CDM samples/timeouts/errors/exceptions: "
              f"{cdm.get('sample_count')} / {cdm.get('timeout_case_count')} / "
              f"{cdm.get('error_case_count')} / {cdm.get('exception_case_count')}")
    if teds:
        print("- TEDS samples/timeouts/errors/exceptions: "
              f"{teds.get('sample_count')} / {teds.get('timeout_case_count')} / "
              f"{teds.get('error_case_count')} / {teds.get('exception_case_count')}")
    if runtime:
        magick_version = magick.split(" | ")[0] if isinstance(magick, str) else magick
        print(f"- runtime: ImageMagick={magick_version}; Ghostscript={gs}; CJK={texlive}")


if __name__ == "__main__":
    main()
