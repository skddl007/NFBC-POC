# Deploying the Web Voice Agent on Render

Render gives you a stable public HTTPS URL **with unrestricted outbound internet**,
so the `/create-web-call` endpoint can reach `api.retellai.com` (unlike PythonAnywhere's
free tier). HTTPS also means the browser will allow microphone access.

The repo already contains everything Render needs:
- `requirements.txt` — `flask` + `gunicorn`
- `Procfile` / `render.yaml` — the start command
- `web/index.html` — the voice UI, served at `/`

---

## 1. Push the project to GitHub

```bash
cd shubhlife
git init            # if it isn't already a repo
git add .
git commit -m "MyShubhLife voice agent"
git branch -M main
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

> `.env` is git-ignored, so your secret key is **not** pushed. You'll set the
> keys in Render's dashboard instead (step 3).

---

## 2. Create the web service on Render

1. Go to https://render.com → **New** → **Web Service**.
2. Connect your GitHub repo.
3. Settings:
   - **Runtime:** Python
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** leave Render's default `gunicorn app:app` — the repo's root
     `app.py` shim points it at `functions/server.py`. (You can also use the more
     explicit `gunicorn --chdir functions server:app` if you prefer.)
   - **Health check path:** `/health`
   - **Plan:** Free

> **Note:** `render.yaml` only applies if you deploy via Render **Blueprints**. If you
> created a regular **Web Service**, that file is ignored and Render uses its default
> start command `gunicorn app:app` — which is why the root `app.py` shim exists.

---

## 3. Set the environment variables (your keys)

In the service's **Environment** tab, add:

| Key | Value |
|-----|-------|
| `RETELL_API_KEY`  | your Retell secret key |
| `RETELL_AGENT_ID` | your Retell agent ID |

Click **Save** — Render redeploys automatically.

---

## 4. Test

Render gives you a URL like `https://myshubhlife-voicebot.onrender.com`.

1. Health check:
   ```
   https://<your-app>.onrender.com/health
   ```
   Expect `"retell_api_key_set": true, "retell_agent_id_set": true`.
2. Open the voice agent:
   ```
   https://<your-app>.onrender.com/
   ```
   Click the mic → allow microphone → start talking.

---

## 5. (Optional) Keep it awake with GitHub Actions

The free tier sleeps after ~15 min idle. The repo includes a workflow at
`.github/workflows/keep-alive.yml` that pings `/health` every 10 minutes to keep it warm.

To enable it:
1. Push the repo to GitHub (the workflow ships with it).
2. In GitHub → **Settings → Secrets and variables → Actions → Variables** tab →
   **New repository variable**:
   - **Name:** `RENDER_URL`
   - **Value:** your Render URL, e.g. `https://myshubhlife-voicebot.onrender.com`
3. Go to the **Actions** tab, enable workflows if prompted, and run **Keep Render awake**
   once manually to confirm it succeeds.

> Notes: GitHub cron can fire a few minutes late, and it pauses scheduled workflows after
> 60 days of repo inactivity (just re-enable). This keeps the instance warm but doesn't
> upgrade the free tier's limits — for a real pilot, use a paid always-on instance.

---

## Notes

- **Free tier sleeps** after ~15 min idle; the first request then takes ~30–50s to wake.
  Fine for a demo; use a paid instance for an always-on pilot (see the keep-alive workflow above).
- Your existing Retell agent (prompt + custom functions) is reused as-is — no extra
  Retell config is needed for web calls beyond having the agent ID.
- If your custom functions also need to be reachable, they're served from the **same**
  app at `/functions/<name>`, so point Retell's function URLs at this Render URL too.
