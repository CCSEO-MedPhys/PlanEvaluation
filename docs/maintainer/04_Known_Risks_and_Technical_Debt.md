# 04 Known Risks and Technical Debt

## 1) Code Quality Risks

- Duplicate imports are present in PlanEvaluation.py, indicating low lint hygiene.
- Some string comparisons use identity style patterns that should be reviewed for correctness.
- Several TODO and FIXME comments indicate unfinished behavior.
- Limited error-handling depth for file parsing and Excel operations.

## 2) Operational Risks

- Strong dependence on Windows and local Excel installation via COM.
- Path defaults can be machine-specific and may break portability.
- Reports.pkl cache can become stale if report XML is changed without rebuilding.
- Distribution folder contains a duplicated source tree, which can drift from root source.

## 3) Clinical Data Risks

- Alias and laterality mapping are highly naming-sensitive.
- Manual direct-entry values can bypass automated derivation logic.
- Constructor parsing assumes specific text formats and may fail silently for unexpected styles.

## 4) Mitigation Priorities

Priority 1
- Add automated regression tests for selected report XML + DVH fixtures.
- Add explicit warning in GUI when ReportDefinitions cache may be stale.

Priority 2
- Remove duplicate imports and add linting step.
- Standardize string comparisons and defensive checks.

Priority 3
- Introduce a single source package build step that populates distribution artifact automatically.
- Improve logging for match failures and unit conversion errors.

## 5) Suggested Minimum Test Dataset

Maintain at least:
- One DVH per major disease site currently used.
- One case with right-sided laterality and one left-sided laterality.
- One intentionally difficult naming case requiring aliases.
- One previously validated reference output workbook for comparison.
