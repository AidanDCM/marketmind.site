# MarketMind local CI test log

Append-only evidence. Do not edit past entries.
## 2026-06-24T23:35:06Z
- Branch: main
- Commit: 79cd7266386cbc853f2efc01efa57c7c891a915f
- Environment: marketmind-local-ci, Python 3.14.5
- Result: FAIL
- Commands:
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pip install --upgrade pip` — ok (13.0s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pip install -e .[dev]` — ok (26.8s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m ruff check .` — FAILED (exit 1) (0.5s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pytest -q --tb=short` — ok (18.3s)
- Failure output: see ruff above
- Follow-up: none
## 2026-06-24T23:38:30Z
- Branch: feat/slice-115-process-and-cac-link
- Commit: 79cd7266386cbc853f2efc01efa57c7c891a915f
- Environment: marketmind-local-ci, Python 3.14.5
- Result: PASS
- Commands:
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pip install --upgrade pip` — ok (6.4s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pip install -e .[dev]` — ok (29.0s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m ruff check .` — ok (0.3s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pytest -q --tb=short` — ok (18.4s)
- Failure output: none
- Follow-up: none
## 2026-06-24T23:46:51Z
- Branch: feat/slice-116-secondary-metrics-risk-links
- Commit: 927a598024035406ba005fe11cbfad203effd937
- Environment: marketmind-local-ci, Python 3.14.5
- Result: PASS
- Commands:
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pip install --upgrade pip` — ok (4.4s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pip install -e .[dev]` — ok (19.8s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m ruff check .` — ok (0.3s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pytest -q --tb=short` — ok (15.3s)
- Failure output: none
- Follow-up: none
## 2026-06-24T23:56:41Z
- Branch: feat/slice-117-conversion-zero-order-link
- Commit: adf0f67a0c2499c8381d7674505c3781af820569
- Environment: marketmind-local-ci, Python 3.14.5
- Result: PASS
- Commands:
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pip install --upgrade pip` — ok (4.2s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pip install -e .[dev]` — ok (18.9s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m ruff check .` — ok (0.2s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pytest -q --tb=short` — ok (14.9s)
- Failure output: none
- Follow-up: none
## 2026-06-25T00:05:20Z
- Branch: feat/slice-118-trend-attention-empty-link
- Commit: cbf24e4f03e07108d78b621937020dd55bacbea0
- Environment: marketmind-local-ci, Python 3.14.5
- Result: PASS
- Commands:
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pip install --upgrade pip` — ok (4.5s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pip install -e .[dev]` — ok (19.6s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m ruff check .` — ok (0.3s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pytest -q --tb=short` — ok (16.6s)
- Failure output: none
- Follow-up: none
## 2026-06-25T00:14:00Z
- Branch: feat/slice-119-overview-no-report-empty-links
- Commit: 51453a0e034b5ecb7bd30d2f79721c9220e9b444
- Environment: marketmind-local-ci, Python 3.14.5
- Result: PASS
- Commands:
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pip install --upgrade pip` — ok (5.0s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pip install -e .[dev]` — ok (20.1s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m ruff check .` — ok (0.3s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pytest -q --tb=short` — ok (15.4s)
- Failure output: none
- Follow-up: none
## 2026-06-25T00:28:56Z
- Branch: harden/phase-b-overview-navigation-audit
- Commit: 169b6c4ab647fb0818e9ed2b5a8a94b2ed31bb5c
- Environment: marketmind-local-ci, Python 3.14.5
- Result: PASS
- Commands:
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pip install --upgrade pip` — ok (5.5s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pip install -e .[dev]` — ok (23.9s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m ruff check .` — ok (0.4s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pytest -q --tb=short` — ok (17.8s)
- Failure output: none
- Follow-up: none
## 2026-06-25T01:00:05Z
- Branch: harden/phase-b-approval-gate
- Commit: 5594dc23b2b451d6fed2c05a9be7225ee40db601
- Environment: marketmind-local-ci, Python 3.14.5
- Result: FAIL
- Commands:
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pip install --upgrade pip` — ok (4.8s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pip install -e .[dev]` — ok (17.8s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m ruff check .` — ok (0.2s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pytest -q --tb=short` — FAILED (exit 1) (12.8s)
- Failure output: see pytest above
- Follow-up: none
## 2026-06-25T01:04:08Z
- Branch: harden/phase-b-approval-gate
- Commit: 5594dc23b2b451d6fed2c05a9be7225ee40db601
- Environment: marketmind-local-ci, Python 3.14.5
- Result: PASS
- Commands:
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pip install --upgrade pip` — ok (6.3s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pip install -e .[dev]` — ok (34.7s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m ruff check .` — ok (0.6s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pytest -q --tb=short` — ok (23.5s)
- Failure output: none
- Follow-up: none
## 2026-06-25T01:16:10Z
- Branch: harden/phase-b-operator-health
- Commit: c7719e3dc0d0d2761ba48377576d354ad2acf29e
- Environment: marketmind-local-ci, Python 3.14.5
- Result: FAIL
- Commands:
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pip install --upgrade pip` — ok (12.0s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pip install -e .[dev]` — ok (24.8s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m ruff check .` — FAILED (exit 1) (0.3s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pytest -q --tb=short` — ok (20.5s)
- Failure output: see ruff above
- Follow-up: none
## 2026-06-25T01:17:49Z
- Branch: harden/phase-b-operator-health
- Commit: c7719e3dc0d0d2761ba48377576d354ad2acf29e
- Environment: marketmind-local-ci, Python 3.14.5
- Result: FAIL
- Commands:
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pip install --upgrade pip` — ok (5.1s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pip install -e .[dev]` — ok (24.0s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m ruff check .` — FAILED (exit 1) (0.3s)
  - `C:\Users\Aidan\AppData\Local\Python\pythoncore-3.14-64\python.exe -m pytest -q --tb=short` — ok (21.9s)
- Failure output: see ruff above
- Follow-up: none
