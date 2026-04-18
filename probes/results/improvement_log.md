# Probe Library Improvement Log

Run `python probes/run_probes.py --update-docs` to add new entries.
Run `python probes/run_probes.py --update-docs --mode fixed` after applying fixes.

---

## Run: 2026-04-18 (baseline)
- **Results file:** run_2026-04-18T17-37-25.json
- **Overall pass rate:** 66% (14/21)
- **Key failures:**
  - Domain Knowledge: probes 4.2, 4.4, 4.5 failed
  - Multi-Category: probes 5.1 failed
  - Multi-DB Routing: probes 1.1, 1.2 failed
  - Text Extraction: probes 3.4 failed

---

## Run: 2026-04-18 (post-fix)
- **Results file:** run_2026-04-18T17-40-24.json
- **Overall pass rate (fixed):** 71% (15/21)
- **Probes now passing:**
  - Domain Knowledge: probes 4.1, 4.3, 4.5 now pass
  - Key Mismatch: probes 2.1, 2.2, 2.3, 2.4, 2.5 now pass
  - Multi-DB Routing: probes 1.3, 1.4, 1.5 now pass
  - Text Extraction: probes 3.1, 3.2, 3.3, 3.5 now pass
- **Still failing:**
  - Domain Knowledge: probes 4.2, 4.4 failed
  - Multi-Category: probes 5.1 failed
  - Multi-DB Routing: probes 1.1, 1.2 failed
  - Text Extraction: probes 3.4 failed
