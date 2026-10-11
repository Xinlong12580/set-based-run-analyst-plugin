# Pinned software semantics

Source: https://github.com/Xinlong12580/Set_Based_Models/tree/90ae91001090110a3689688bfde6140584ede102
Reviewed: docs/AI_GUIDE.md, docs/REPORT_FORMAT.md, schemas/quantitative_report.schema.json, reports/ERL_implementation.md, raw_event_conversion/{README.md,PAIRS.md,IMPACT_PARAMETERS.md}, examples/reports/{README.md,erl_synthetic.json,edt_synthetic.json}; runner configuration and rule_list/pruning.py. Fixtures are hand-authored structural examples, not measured results. Do not use their stored-label discussions.

## Metrics, scoring and rates

`signal_*` fields mean anomalous-mixture input membership; `background_*` means reference membership. Source keys are retained for citations, while filenames are replaced with mixture_A/reference_A. Purity = accepted mixture / accepted combined inputs, zero for empty selections. Acceptance ratios are null when reference acceptance is zero. Count-based acceptances need not equal custom weighted scores.

ERL Gini is the gain for the whole conjunction versus its complement on original input totals. The flexible runner score is Gini minus reference_penalty times reference acceptance. Negative finite scores are valid. Raw Gini is not directional; inspect both acceptances. Old pure-Gini ERL uses gini_gain when score is absent. Each prefix score is a whole-prefix score, not the last cut's incremental gain; differences may be computed between adjacent scores.

Rate[kHz] = reference acceptance × input_rate_mhz × 1000. The stream must be representative; no default 40 MHz is assumed. At 40 MHz, 40 kHz means 0.001 acceptance. Zero observed passes is not zero physical rate. A per-rule ceiling does not constrain an ERL OR menu. Without event masks ERL union acceptance is unavailable. Leaves of one complete EDT tree partition its dataset and may be summed.

## ERL predicates and pruning

Conjoin ordered cuts with AND. Every slot cut in one rule must match the same slot; minimum_count is the number of slots satisfying the whole conjunction. Event-only conditions ignore slot multiplicity. Distinct rules may overlap and combine by OR. Retain raw numeric comparisons; integer `n > 1.5` means `n >= 2`, not `n > 2`.

A validity guard requires its named Boolean to be true in the same scope. Never infer guards from a suffix or a current conversion default. Automatic guards consume no depth. Padding and measurement invalidity are different. Pair slots contain two distinct members; matching pairs may share a member, so two passing pairs do not imply four particles.

Object priority uses original ordered cuts, including repetitions and directions. Event cuts do not consume object priority. Optional completion filters final eligibility; incomplete prefixes remain searched. Simplification may merge repeated cuts but does not change priority progress.

Current flexible final order: completion eligibility, rate eligibility, equivalence, stricter-score filtering, final similarity. Read recorded policy before applying this order to older runners. `retained_after_final_pruning` is authoritative when present. Flexible-runner nested/similarity retention flags are final aliases, not independent histories. With only legacy flags and no policy, final retention can be described but the responsible stage is unknown.

- incomplete_object_priority: final completion requirement not met, no witness.
- reference_rate_limit: per-rule budget exceeded, no witness.
- equivalent_rule: a logically equivalent representative was selected.
- stricter_score_improvement: a stricter rule failed the signed improvement test versus a looser witness.
- similarity: empirical accepted-event overlap filtering, not proven containment.
- retained: final survivor.

Logical retention requires strict-minus-loose score > signed threshold; equality is removed with 1e-12 relative/absolute roundoff tolerance. Negative thresholds permit bounded score loss without changing ranking or disabling other filters. score_gap = witness minus removed score; score_improvement has the opposite sign. pruned_by_rule_id is the direct witness; retained_witness_rule_id follows the chain to the final survivor. IDs are local to one pool. Logical containment uses same-column predicates, not inferred correlations between different physical features. Search-time beam similarity is separate from final filtering. Final reports do not enumerate every lost expansion.

## EDT branches

The stored cut is the positive test. A negative branch negates the ENTIRE guarded condition: NOT(guard AND measurement), potentially accepting invalid measurements. Object branches depend on inherited surviving-slot state; do not rebuild them as independent existential cuts. Leaf fractions rank training mixture composition; split gains are local to the node, not ERL scores. Default prediction is set by decision_threshold and may differ from enrichment direction when input sizes differ. The event-only loader in this retrieved version does not automatically enable validity guards: inspect runtime observables and recorded flags.

## Feature definitions and reconstruction limits

Object category codes must use recorded maps, not universal assumptions. Saved units/definitions must be present and match the vetted catalog to be emitted; missing values are unknown. The catalog covers 193 default event features, 20 object features and 68 pair features at the retrieved revision, without requiring those widths at runtime. Custom features are deliberately anonymized and withheld from interpretation.

Current converter event summaries use full stored collections, while object/pair arrays use capped objects. Total scalar PT is not overlap-cleaned HT or producer ScalarHT. Ranked coordinates refer to the PT-ranked object; invalid coordinates do not promote another object. Pair member order is type first then PT within type. Pair presence and measurement guards must both hold. No tensor behavior is evaluated by this report-only plugin.

Producer D0 is beam-spot/origin referenced, not a reconstructed-PV impact parameter or a decay radius. The audited production in IMPACT_PARAMETERS.md uses mm and had zero PF ErrorD0 in a limited shard check, with no executed TrackSmearing. This does not establish behavior of every run. Missingness/padding, collection overlaps, truncation, pileup and producer choices can explain separation. Avoid interpreting unavailable significance or displacement alone as realistic trigger performance.

## Blinding contract

Explicit allowlist projection rejects arbitrary model-facing strings. Dataset paths, names, free-text rules, label maps, injected fractions, selected/stored label counts, timestamps and arbitrary metadata are not emitted. Unknown names receive stable positional aliases. Physical category strings have a fixed vocabulary. Feature metadata mentioning process/truth/generator/label/injected content makes that feature unusable. No automatic unblinding exists. The host may expose attachments before this skill runs; disclose that limitation if it occurs.

The original schema is adapted only to stop requiring/validating discarded text and label fields. Structural and numeric fields are validated. An internal stdlib validator implements the schema's used keywords; it is not a general JSON Schema engine. Arithmetic warnings identify neutral field paths, never raw values or exception text. Strict JSON rejects duplicate keys and NaN/Infinity, bounds input size, and suppresses raw exceptions. Deliberately encoded covert information in numeric observables is outside this blinding guarantee.
