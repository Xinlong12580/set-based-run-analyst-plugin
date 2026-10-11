# Blinded synthetic demonstration

Evidence: report-only. These are hand-authored structural fixtures, not physics results or validation.

| ERL rule | Global / retained rank | Same-object condition | Mixture passes | Reference passes | Score | Status |
|---|---|---|---|---|---|---|
| 0 | 1 / 1 | Photon, PT >25 GeV | 20/100 (20%) | 0/100 (0%) | 0.055556 | Retained |
| 1 | 2 / — | Photon, PT >25 then >35 GeV | 15/100 (15%) | 0/100 (0%) | 0.040541 | Stricter-score filter; witness 0 |
| 2 | 3 / — | Photon | 30/100 (30%) | 4/100 (4%) | 0.019887 | Priority incomplete |

Rule 1 has original depth 3, simplified depth 2. It loses five mixture events without reducing observed reference passes. Its whole-rule score falls by 0.015015 relative to rule 0, failing the configured strictly positive improvement. A threshold of -0.02 would pass this particular logical test holding the scores fixed; it would not guarantee final retention under other filters. Rule 2 has the largest raw Gini (0.059887), but its 0.04 penalty lowers its optimization score. Completion, rather than similarity, is its recorded removal reason.

The reported 40 MHz stream assumption gives empirical rates 0, 0 and 1600 kHz. Zero reference passes among 100 events does not establish zero physical rate. No rate ceiling or independent validation is supplied. Mixture acceptance and training-class purity say nothing about unknown component identity or efficiency. An ERL OR acceptance cannot be calculated from these marginal counts.

For EDT, leaf 1 selects n_photons_pt20 >0.5 (at least one), with 30/100 mixture and 4/100 reference passes. The negative leaf selects no such photons, with 70/100 and 96/100. Its stored cut still describes the positive test; the branch determines the negation. Both leaves partition the input. At threshold 0.5, only leaf 1 is predicted positive. A guarded negative branch would negate the entire guard AND measurement, not merely reverse the threshold.

Next checks: independently evaluate the fixed selection on a much larger representative reference sample, establish reconstruction/guard behavior, and evaluate event masks before combining ERL rules.

Citations: run_A results.rules[0..2].metrics, .steps, .pruning; run_B results.leaves[0..1].path and .metrics; docs/REPORT_FORMAT.md and rule_list/pruning.py at 90ae91001090110a3689688bfde6140584ede102.
