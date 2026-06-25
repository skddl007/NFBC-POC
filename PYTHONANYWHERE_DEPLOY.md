# Deploying the MyShubhLife Voice Bot Backend on PythonAnywhere

This gives you a **stable public HTTPS URL** for your 11 Retell webhook functions —
no ngrok, no laptop kept running. Free tier is enough for this POC.

Your URL will be: `https://<username>.pythonanywhere.com`

---

## 0. What gets deployed

Only the Flask backend (`functions/server.py` + `data/customers.json`).
The system prompt and function schemas are still pasted into Retell as before.

```
shubhlife/
├── functions/server.py        # the Flask app (`app`)
├── data/customers.json         # synthetic data it reads
├── requirements.txt            # flask==3.0.0
└── wsgi_pythonanywhere.py      # WSGI entry — paste into PA's WSGI config
```

---

## 1. Create a PythonAnywhere account

1. Sign up (free "Beginner" plan) at https://www.pythonanywhere.com
2. Verify email and log in to the Dashboard.

---

## 2. Upload the project

### Option A — Upload a ZIP (simplest)
1. On your PC, zip the `shubhlife` folder.
2. PythonAnywhere → **Files** tab → upload the zip into `/home/<username>/`.
3. Open a **Bash console** (Consoles tab) and unzip:
   ```bash
   cd ~
   unzip shubhlife.zip
   ls shubhlife        # should show functions/ data/ etc.
   ```

### Option B — Clone from Git (if you push this to GitHub)
```bash
cd ~
git clone <your-repo-url> shubhlife
```

After this you should have: `/home/<username>/shubhlife/functions/server.py`

---

## 3. Install Flask

In a **Bash console**:
```bash
pip install --user flask==3.0.0
```
(Or use a virtualenv — see step 6 if you prefer.)

---

## 4. Create the web app

1. Go to the **Web** tab → **Add a new web app**.
2. Domain: accept `https://<username>.pythonanywhere.com` → **Next**.
3. Framework: choose **Manual configuration** (NOT "Flask" — we supply our own WSGI).
4. Python version: pick **3.10** or newer → **Next**.

---

## 5. Point the WSGI file at the app

1. On the **Web** tab, find **"WSGI configuration file"** — it's a link like:
   `/var/www/<username>_pythonanywhere_com_wsgi.py`
2. Click it to open the editor.
3. **Delete everything** in that file.
4. Open `wsgi_pythonanywhere.py` from this project, copy its contents, and paste them in.
5. Change this line to your real username:
   ```python
   USERNAME = "yourusername"
   ```
6. **Save**.

> This adds `/home/<username>/shubhlife/functions` to the path and imports
> `app` from `server.py` as `application`, which is what PythonAnywhere runs.

---

## 6. (Optional but recommended) Use a virtualenv

If `pip install --user` gives version conflicts, use a clean virtualenv:

```bash
mkvirtualenv shubhlife-env --python=/usr/bin/python3.10
pip install flask==3.0.0
```

Then on the **Web** tab → **Virtualenv** section, enter:
```
/home/<username>/.virtualenvs/shubhlife-env
```

---

## 7. Reload and test

1. **Web** tab → big green **Reload** button.
2. Open in a browser:
   ```
   https://<username>.pythonanywhere.com/health
   ```
   Expected:
   ```json
   {"status": "ok", "customers_loaded": 20}
   ```
3. Test a function endpoint (use a POST tool, browser GET will show 405):
   ```bash
   curl -X POST https://<username>.pythonanywhere.com/functions/lookup_customer_by_mobile \
     -H "Content-Type: application/json" \
     -d '{"mobile_number":"9982385483"}'
   ```
   Expected: Sandeep Kumar / CUST001 found.

---

## 8. Update Retell with the new URLs

Replace your ngrok base with the PythonAnywhere base in all 11 functions:

Base URL: `https://<username>.pythonanywhere.com`

| Function | URL |
|----------|-----|
| lookup_customer_by_mobile | `.../functions/lookup_customer_by_mobile` |
| verify_identity | `.../functions/verify_identity` |
| get_loan_details | `.../functions/get_loan_details` |
| get_payment_history | `.../functions/get_payment_history` |
| check_loan_eligibility | `.../functions/check_loan_eligibility` |
| check_advance_payment_eligibility | `.../functions/check_advance_payment_eligibility` |
| get_foreclosure_quote | `.../functions/get_foreclosure_quote` |
| initiate_payment_link | `.../functions/initiate_payment_link` |
| send_statement | `.../functions/send_statement` |
| log_fraud_report | `.../functions/log_fraud_report` |
| escalate_to_agent | `.../functions/escalate_to_agent` |

All **POST**.

---

## 9. Where to see logs

On the **Web** tab there are three log links:
- **Access log** — every incoming Retell request
- **Error log** — Python tracebacks if something breaks
- **Server log** — the `print()` output (simulated SMS, fraud log, escalations)

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `/health` 502/500 | Check **Error log**. Usually wrong `USERNAME` or path in WSGI file. |
| `ModuleNotFoundError: server` | `PROJECT_FUNCTIONS_DIR` path wrong — must point to the folder holding `server.py`. |
| `FileNotFoundError: customers.json` | Folder structure broken — `data/` must sit next to `functions/`. |
| `No module named flask` | Run `pip install --user flask==3.0.0`, or set the virtualenv on the Web tab. |
| 405 on a function URL in browser | Normal — endpoints are POST-only. Use curl/Retell. |
| Changes not taking effect | Click **Reload** on the Web tab after every edit. |

---

## 10. Web Voice Agent (talk to the bot from a browser)

A browser-based voice UI is served at the site root (`/`). Visitors click the mic,
allow their microphone, and talk to the Retell agent live — no phone call needed.

### How it works
- `web/index.html` loads the Retell Web SDK and calls the backend at `/create-web-call`.
- `/create-web-call` (in `server.py`) calls Retell with your **secret** API key and returns
  only a short-lived `access_token` to the browser. The API key never reaches the client.

### Required environment variables
Set these so `/create-web-call` works:

| Variable | Where to find it |
|----------|------------------|
| `RETELL_API_KEY`  | Retell Dashboard → **API Keys** (the secret key) |
| `RETELL_AGENT_ID` | Retell Dashboard → your Agent → the agent's ID |

**Local (PowerShell):**
```powershell
$env:RETELL_API_KEY="key_xxxxxxxx"
$env:RETELL_AGENT_ID="agent_xxxxxxxx"
python functions/server.py
# then open http://localhost:5000/
```

**Local (bash):**
```bash
export RETELL_API_KEY="key_xxxxxxxx"
export RETELL_AGENT_ID="agent_xxxxxxxx"
python3 functions/server.py
```

**PythonAnywhere:** add both vars near the top of the WSGI file before importing the app, e.g.:
```python
import os
os.environ["RETELL_API_KEY"]  = "key_xxxxxxxx"
os.environ["RETELL_AGENT_ID"] = "agent_xxxxxxxx"
```
Then **Reload**. Confirm via `/health` — it shows `retell_api_key_set` / `retell_agent_id_set`.

> Microphone access requires HTTPS (or `localhost`). PythonAnywhere serves HTTPS, so it works there.

---

## Notes / limits (free tier)

- **Always-on URL** — no need to keep your PC or ngrok running.
- **Outbound internet is whitelisted** on free tier, but this app makes **no** outbound calls (payments/SMS are simulated), so it's unaffected.
- **Fraud log is in-memory** — resets whenever the web app reloads. Fine for a POC.
- For production, you'd still swap `customers.json` for a real API and add webhook auth.
