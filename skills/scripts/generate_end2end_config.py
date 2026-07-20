#!/usr/bin/env python3
"""Generate an OmniDocBench end2end config for community users."""

import argparse
from pathlib import Path

import yaml


def main():
    parser = argparse.ArgumentParser(description="Generate configs/custom_end2end.yaml for OmniDocBench.")
    parser.add_argument("--gt", required=True, help="Ground-truth OmniDocBench JSON path as seen by the runtime")
    parser.add_argument("--pred", required=True, help="Prediction markdown folder path as seen by the runtime")
    parser.add_argument("--out", default="configs/custom_end2end.yaml", help="Output YAML path")
    parser.add_argument("--workers", type=int, default=4, help="Worker count for match/CDM/TEDS stages")
    parser.add_argument("--no-cdm", action="store_true", help="Disable CDM to avoid TeX/ImageMagick/Ghostscript requirements")
    args = parser.parse_args()

    if args.workers < 1:
        raise SystemExit("--workers must be >= 1")

    display_formula_metrics = ["Edit_dist"] if args.no_cdm else ["Edit_dist", "CDM"]
    config = {
        "end2end_eval": {
            "metrics": {
                "text_block": {"metric": ["Edit_dist"]},
                "display_formula": {"metric": display_formula_metrics},
                "table": {"metric": ["TEDS", "Edit_dist"]},
                "reading_order": {"metric": ["Edit_dist"]},
            },
            "dataset": {
                "dataset_name": "end2end_dataset",
                "ground_truth": {"data_path": args.gt},
                "prediction": {"data_path": args.pred},
                "match_method": "quick_match",
                "match_workers": args.workers,
                "quick_match_truncated_timeout_sec": 300,
                "match_timeout_sec": 420,
                "timeout_fallback_max_chunk_span": 10,
                "timeout_fallback_order_penalty": 0.10,
            },
        }
    }

    if not args.no_cdm:
        config["end2end_eval"]["metrics"]["display_formula"]["cdm_workers"] = args.workers
    config["end2end_eval"]["metrics"]["table"]["teds_workers"] = args.workers

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, allow_unicode=True, sort_keys=False)
    print(out_path)


if __name__ == "__main__":
    main()
