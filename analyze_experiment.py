#!/usr/bin/env python3
"""Analyze the onboarding experiment and write answers.json.

Usage:
    python3 analyze_experiment.py experiment_results-2.csv

If no CSV path is passed, the script tries experiment_results.csv first and then
experiment_results-2.csv. It uses only the Python standard library.
"""

import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path


def rate(successes, total):
    return successes / total


def lift_pp(control_successes, control_n, treatment_successes, treatment_n):
    return 100 * (
        rate(treatment_successes, treatment_n)
        - rate(control_successes, control_n)
    )


def wald_ci_pp(control_successes, control_n, treatment_successes, treatment_n):
    """Approximate 95% CI for treatment rate minus control rate, in pp."""
    p_control = rate(control_successes, control_n)
    p_treatment = rate(treatment_successes, treatment_n)
    difference = p_treatment - p_control
    standard_error = math.sqrt(
        p_control * (1 - p_control) / control_n
        + p_treatment * (1 - p_treatment) / treatment_n
    )
    return 100 * (difference - 1.96 * standard_error), 100 * (difference + 1.96 * standard_error)


def choose_csv_path():
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    for name in ("experiment_results.csv", "experiment_results-2.csv"):
        path = Path(name)
        if path.exists():
            return path
    raise FileNotFoundError("Pass the CSV path: python3 analyze_experiment.py experiment_results.csv")


def main():
    csv_path = choose_csv_path()
    overall = defaultdict(lambda: {"n": 0, "converted": 0})
    by_segment = defaultdict(lambda: defaultdict(lambda: {"n": 0, "converted": 0}))
    segment_total = defaultdict(int)
    seen_user_ids = set()

    with csv_path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        expected_columns = {"user_id", "segment", "variant", "converted"}
        if set(reader.fieldnames or []) != expected_columns:
            raise ValueError(f"Expected columns {sorted(expected_columns)}; got {reader.fieldnames}")

        for row in reader:
            user_id = row["user_id"]
            segment = row["segment"]
            variant = row["variant"]
            converted = int(row["converted"])

            if user_id in seen_user_ids:
                raise ValueError(f"Duplicate user_id found: {user_id}")
            seen_user_ids.add(user_id)
            if variant not in {"control", "treatment"}:
                raise ValueError(f"Unexpected variant: {variant}")
            if converted not in {0, 1}:
                raise ValueError(f"converted must be 0 or 1; got {converted}")

            overall[variant]["n"] += 1
            overall[variant]["converted"] += converted
            by_segment[segment][variant]["n"] += 1
            by_segment[segment][variant]["converted"] += converted
            segment_total[segment] += 1

    if set(overall) != {"control", "treatment"}:
        raise ValueError("Both control and treatment must be present")

    control = overall["control"]
    treatment = overall["treatment"]
    total_users = control["n"] + treatment["n"]
    naive_lift = lift_pp(
        control["converted"], control["n"],
        treatment["converted"], treatment["n"],
    )

    segment_results = {}
    weighted_lift = 0.0
    for segment in sorted(by_segment):
        control_group = by_segment[segment]["control"]
        treatment_group = by_segment[segment]["treatment"]
        if control_group["n"] == 0 or treatment_group["n"] == 0:
            raise ValueError(f"Segment {segment} is missing one variant")

        segment_lift = lift_pp(
            control_group["converted"], control_group["n"],
            treatment_group["converted"], treatment_group["n"],
        )
        ci_low, ci_high = wald_ci_pp(
            control_group["converted"], control_group["n"],
            treatment_group["converted"], treatment_group["n"],
        )
        population_weight = segment_total[segment] / total_users
        weighted_lift += population_weight * segment_lift
        segment_results[segment] = {
            "total_n": segment_total[segment],
            "control_n": control_group["n"],
            "control_rate_pct": 100 * rate(control_group["converted"], control_group["n"]),
            "treatment_n": treatment_group["n"],
            "treatment_rate_pct": 100 * rate(treatment_group["converted"], treatment_group["n"]),
            "lift_pp": segment_lift,
            "ci_95_pp": [ci_low, ci_high],
            "treatment_share_pct": 100 * treatment_group["n"] / segment_total[segment],
        }

    # Q2 rule: flag the segment with the least evidence. Here it is influencer,
    # with only 250 total users and a wide interval crossing zero.
    untrustworthy_segment = min(segment_results, key=lambda segment: segment_results[segment]["total_n"])

    # Q4 rule: select the largest positive lift whose approximate 95% CI is
    # entirely above zero. Here this identifies app_store.
    credible_positive_segments = [
        segment for segment, result in segment_results.items()
        if result["lift_pp"] > 0 and result["ci_95_pp"][0] > 0
    ]
    real_effect_segment = max(
        credible_positive_segments,
        key=lambda segment: segment_results[segment]["lift_pp"],
    ) if credible_positive_segments else "none"

    answers = {
        "q1_naive_lift_pp": naive_lift,
        "q1_n_control": control["n"],
        "q1_n_treatment": treatment["n"],
        "q2_untrustworthy_segment": untrustworthy_segment,
        "q3_mix_adjusted_lift_pp": round(weighted_lift, 2),
        "q4_real_effect_segment": real_effect_segment,
    }

    with Path("answers.json").open("w", encoding="utf-8") as file:
        json.dump(answers, file, indent=2)
        file.write("\n")

    print(json.dumps(answers, indent=2))
    print("\nSegment diagnostics:")
    for segment, result in segment_results.items():
        print(
            f"{segment}: n={result['total_n']}, "
            f"lift={result['lift_pp']:.4f} pp, "
            f"95% CI=({result['ci_95_pp'][0]:.2f}, {result['ci_95_pp'][1]:.2f}) pp, "
            f"treatment share={result['treatment_share_pct']:.2f}%"
        )


if __name__ == "__main__":
    main()