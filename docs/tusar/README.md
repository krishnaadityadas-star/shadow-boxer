# Shadow-Boxer — Tushar's Testing & Documentation

Prepared for integration into the project's `docs/tushar/` directory. Includes Tushar's original documents and updated browser-readable GitHub Markdown versions.

| File | Purpose |
|---|---|
| [Baseline Testing Report — 13 Nov](BASELINE_TEST_REPORT_2026-11-13.md) | Historical Windows setup, keyboard and four original webcam gesture checks. **Original observations preserved**. |
| [Project Documentation & Windows Setup](PROJECT_AND_WINDOWS_SETUP.md) | Current architecture, controls, file guide, Windows installation, and verification status. |
| [Demo Plan & Evidence Guide](DEMO_PLAN_AND_EVIDENCE.md) | Four-minute demo flow, feature checklist, media checklist, and caveats. |
| [Combat Validation Update — 14 Nov](VALIDATION_UPDATE_2026-11-14.md) | Explicitly separates later live forward-punch confirmation from older Windows baseline. |
| [`original_docx/`](original_docx/) | Three original Word reports supplied by Tushar, preserved without edits for authorship/history. |

## Key distinction

**13 Nov:** Tushar independently tested an earlier repository snapshot (`e9f0a58`) on Windows. His baseline **did not** establish working webcam PUNCH or BLOCK. It did report a slight playable response delay and leave touch and long-duration tests unverified.

**14 Nov:** Krishna confirmed forward-punch registration and guard feedback on a newer integration; separate automated/recorded-data regression checks were logged in the project's root `TEST_RESULTS.txt`.

The updated guides do not retroactively alter Tushar's historical test outcomes. The sweep mechanic is in code but remains pending final gameplay validation.

**Integration note:** No Python game files or model files are included in this documentation package.
