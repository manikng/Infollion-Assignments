# Onboarding Experiment Investigation

## Reasoning approach

For this investigation, I used two personal reasoning frameworks. I built these frameworks from my experience of solving technical problems and observing how I can avoid jumping to conclusions too early.

**SEARCH** means Structured Exploration & Analysis for Reasoning toward a Solution Hypothesis. I use it to understand the structure first, inspect high-information cases, compare relationships, form a hypothesis, and test it against counterexamples or boundary cases. Here, it helped me move from the headline lift to the segment-level pattern and assignment imbalance.

**FORGE** means Framework for Organizing Reasoning, Guarding Execution. I use it to frame the exact input and output, organize calculations, verify assumptions and edge cases, and explain the final conclusion clearly. Here, it helped me keep counts, rate formulas, weights, and assignment-share checks separate and reproducible.

The frameworks guide my investigation. The numbers and conclusions below come directly from the CSV calculations.

## 1. Overall naive comparison

Control has 7,136 users. It has 1,414 conversions.

Control conversion rate:

`1414 / 7136 × 100 = 19.815022421524663%`.

Treatment has 6,864 users. It has 1,814 conversions.

Treatment conversion rate:

`1814 / 6864 × 100 = 26.427738927738925%`.

Naive overall lift:

`26.427738927738925 - 19.815022421524663 = 6.612716506214261 percentage points`.

| Variant | Users | Converted users | Conversion rate |
|---|---:|---:|---:|
| Control | 7,136 | 1,414 | 19.815022421524663% |
| Treatment | 6,864 | 1,814 | 26.427738927738925% |

Therefore, the naive treatment lift is **+6.612716506214261 percentage points**.

## 2. Segment comparison

For every segment, I used:

`segment lift = treatment conversion rate - control conversion rate`.

| Segment | Control n | Control conversions | Control rate | Treatment n | Treatment conversions | Treatment rate | Lift |
|---|---:|---:|---:|---:|---:|---:|---:|
| app_store | 925 | 81 | 8.7568% | 960 | 192 | 20.0000% | +11.2432 pp |
| influencer | 119 | 28 | 23.5294% | 131 | 22 | 16.7939% | -6.7355 pp |
| organic | 1,298 | 458 | 35.2851% | 2,917 | 1,023 | 35.0703% | -0.2148 pp |
| paid_search | 3,353 | 509 | 15.1804% | 1,459 | 210 | 14.3934% | -0.7870 pp |
| referral | 1,441 | 338 | 23.4559% | 1,397 | 367 | 26.2706% | +2.8146 pp |

The segment I would not trust is **influencer**.

Its estimated effect looks large in magnitude at `-6.7355 pp`. But it only has 250 users in total. It has 119 control users and 131 treatment users. This is the smallest segment. The estimate is noisy. Its approximate 95% confidence interval is `-16.69 pp` to `+3.22 pp`. It includes zero.

I would not conclude that the new flow is harmful for influencer users from this dataset alone.

## 3. Mix-adjusted overall lift

I used each segment's share of all 14,000 users as the weight. I did not use the treatment share inside that segment.

`mix-adjusted lift = Σ(segment lift × segment total users / 14,000)`.

| Segment | Total users | Population weight | Segment lift | Weighted contribution |
|---|---:|---:|---:|---:|
| app_store | 1,885 | 13.4643% | +11.2432 pp | +1.5138 pp |
| influencer | 250 | 1.7857% | -6.7355 pp | -0.1203 pp |
| organic | 4,215 | 30.1071% | -0.2148 pp | -0.0647 pp |
| paid_search | 4,812 | 34.3714% | -0.7870 pp | -0.2705 pp |
| referral | 2,838 | 20.2714% | +2.8146 pp | +0.5706 pp |

The unrounded weighted sum is `1.6289429305586989 pp`.

Therefore, the mix-adjusted overall lift is **+1.63 percentage points**.

This is lower than the naive `+6.6127 pp` result because treatment and control do not have the same segment mix. Treatment contains many more organic users. Control contains many more paid-search users. Organic users convert at about 35% in both variants. Paid-search users convert at about 15% in both variants. Therefore, the naive number partly measures user mix instead of only onboarding performance.

## 4. Meaningful positive effect

I believe **app_store** has a real and meaningful positive effect.

Control converts at `81 / 925 = 8.7568%`.

Treatment converts at `192 / 960 = 20.0000%`.

The lift is `20.0000 - 8.7568 = +11.2432 pp`.

This is large in absolute terms. It is based on 1,885 users. The segment is also nearly balanced, with 925 control users and 960 treatment users. Its approximate 95% confidence interval is `+8.13 pp` to `+14.36 pp`. The interval stays above zero.

Referral is also positive at `+2.8146 pp`. But I would not call it confirmed yet. Its approximate 95% confidence interval is `-0.37 pp` to `+5.99 pp`. It includes zero.

## 5. Assignment sanity check

I calculated treatment share as:

`treatment share = treatment users in segment / total users in segment`.

| Segment | Control users | Treatment users | Control share | Treatment share |
|---|---:|---:|---:|---:|
| app_store | 925 | 960 | 49.0716% | 50.9284% |
| influencer | 119 | 131 | 47.6000% | 52.4000% |
| organic | 1,298 | 2,917 | 30.7948% | 69.2052% |
| paid_search | 3,353 | 1,459 | 69.6800% | 30.3200% |
| referral | 1,441 | 1,397 | 50.7752% | 49.2248% |

Yes. The assignment looks off.

App_store, influencer, and referral are close to a 50/50 split. But organic and paid_search are strongly imbalanced.

Organic users were assigned to treatment 69.2052% of the time. Paid-search users were assigned to treatment only 30.3200% of the time.

Organic has about a 35% conversion rate in both variants. Paid-search has about a 15% conversion rate in both variants. Treatment received more high-converting organic users. Control received more lower-converting paid-search users. This makes the raw overall treatment lift look larger than the mix-adjusted estimate.

This is a Simpson's-paradox-style aggregation issue. More precisely, it is an assignment-mix imbalance that distorts the top-line result.

## Investigation process

- **SEARCH — Structure.** I checked the dataset structure first. There are 14,000 rows, 5 segments, and 2 variants.
- **FORGE — Guard.** I checked data quality. There are no missing values. All 14,000 user IDs are unique. `converted` contains only 0 and 1.
- **SEARCH — Examine.** I calculated the full-file conversion rates. This gave the initial `+6.612716506214261 pp` treatment lift.
- **SEARCH — Analyze.** I broke the comparison down by segment. The strong overall result was not repeated in organic or paid_search.
- **SEARCH — Relations.** I compared baseline conversion levels. Organic is around 35%. Paid-search is around 15%. These are different user populations.
- **SEARCH — Hypothesize.** I suspected segment-mix imbalance. The mix-adjusted lift dropped to `+1.63 pp`, which supported this explanation.
- **FORGE — Organize.** I calculated every rate from raw conversion counts. I did not calculate from rounded percentages.
- **FORGE — Guard.** I checked the treatment and control shares within each segment. Organic and paid_search had a major sample-ratio imbalance.
- **FORGE — Guard.** I examined influencer as a possible negative treatment effect. This was a dead end because it has only 250 users and its confidence interval includes zero.
- **FORGE — Explain.** I found credible positive evidence for app_store. I would investigate the assignment issue or rerun a properly stratified experiment before making a global rollout decision.

## Final answers for `answers.json`

```json
{
  "q1_naive_lift_pp": 6.612716506214261,
  "q1_n_control": 7136,
  "q1_n_treatment": 6864,
  "q2_untrustworthy_segment": "influencer",
  "q3_mix_adjusted_lift_pp": 1.63,
  "q4_real_effect_segment": "app_store"
}
```
