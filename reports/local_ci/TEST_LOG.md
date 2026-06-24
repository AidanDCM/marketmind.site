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
