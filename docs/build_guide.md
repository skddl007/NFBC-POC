# MyShubhLife Voice Bot — Retell POC Build Guide

This is a stepwise guide to build, demo, and harden the MyShubhLife loan-support voicebot entirely on Retell AI, using only the files in this project (no other external platform required for the POC).

---

## 0. What you're building

A voice agent that:
1. Answers inbound calls about loan amount, EMIs paid, eligibility for a next loan, advance/partial EMI payment, foreclosure, KYC holds, and general company FAQs.
2. Verifies caller identity before sharing any data.
3. Handles different caller tones (calm, anxious, confused, abusive, distressed) with the right guardrail behavior for each.
4. Escalates to a human agent (MyShubhLife support) whenever it can't or shouldn't handle something itself.
5. Runs entirely on synthetic data (20 customers) so nothing real is at risk during the demo.

### Files in this project
```
shubhlife/
├── data/
│   └── customers.json              # 20 synthetic customers, arithmetic-validated
├── prompts/
│   └── retell_system_prompt.md     # Paste into Retell Agent "General Prompt"
├── functions/
│   ├── retell_function_schemas.json # Paste into Retell "Custom Functions" tab
│   └── server.py                    # Flask backend implementing those functions
└── docs/
    ├── demo_call_scripts.md        # Ready-made demo scripts per persona
    └── build_guide.md              # This file
```

---

## 1. Account & project setup on Retell

1. Sign up / log in at retellai.com and create a new Agent.
2. Choose a voice. For this customer segment, prefer a warm, clear Hindi/Indian-English voice. Retell's voice catalog and multilingual support change frequently — check Retell's current docs/voice list in-app before finalizing, since exact voice names aren't something to assume from memory.
3. Pick an LLM engine in Retell's "Response Engine" settings (Retell supports bringing your own LLM choice — GPT-4o class or similar). Set temperature low (0.3–0.4) since this is a transactional support bot, not a creative one.
4. Set the agent's language/locale options to match the languages you want to demo (Hindi + English minimum; add Tamil/Kannada/Punjabi/Bengali/Malayalam if your Retell plan's voice/STT supports them — verify current language coverage in Retell's docs before promising this in the demo).

---

## 2. Load the system prompt

1. Open `prompts/retell_system_prompt.md`.
2. Copy its full contents into the Agent's "General Prompt" / persona field in Retell.
3. Keep the prompt's structure intact (the headers act as the bot's internal checklist — verification, intent mapping, guardrails, escalation rules). Don't compress it into a single paragraph; Retell's LLM follows structured prompts more reliably than dense prose.

---

## 3. Deploy the backend and wire up Custom Functions

The bot needs somewhere to actually look up loan data — Retell calls out to your webhook for each "Custom Function."

### 3a. Run the backend
```bash
cd shubhlife/functions
pip install flask --break-system-packages
python3 server.py
```
This starts a local server on port 5000 implementing every function in `retell_function_schemas.json` against `data/customers.json`.

### 3b. Expose it to the internet (required — Retell can't reach your laptop directly)
Fastest option for a live demo:
```bash
ngrok http 5000
```
This gives you a public HTTPS URL like `https://abcd1234.ngrok-free.app`. For anything beyond a single demo session, deploy `server.py` to Render, Railway, Fly.io, or any small VM instead, so the URL is stable.

### 3c. Register each function in Retell
1. Open `functions/retell_function_schemas.json`.
2. In Retell's Agent → Functions/Tools tab, add a new Custom Function for each entry in that file.
3. For each one:
   - **Name**: copy exactly (e.g. `lookup_customer_by_mobile`) — the system prompt refers to these names directly.
   - **Description**: copy from the JSON — this is what the LLM uses to decide *when* to call it.
   - **Parameters**: copy the parameter schema.
   - **URL**: `https://<your-ngrok-or-deployed-url>/functions/<function_name>`
   - **Method**: POST
4. Repeat for all 11 functions: `lookup_customer_by_mobile`, `verify_identity`, `get_loan_details`, `get_payment_history`, `check_loan_eligibility`, `check_advance_payment_eligibility`, `get_foreclosure_quote`, `initiate_payment_link`, `send_statement`, `log_fraud_report`, `escalate_to_agent`.

> **Retell's exact function-config UI/fields may have changed.** Before wiring this up, open Retell's current docs for "Custom Functions" / "Tools" in-app and confirm the request/response shape — `server.py`'s `get_args()` is written to tolerantly accept either `{"args": {...}}` or a flat body, but double-check against what your Retell version actually sends.

### 3d. Wire up call transfer for `escalate_to_agent`
Retell has a native **Transfer Call** feature for handing off to a human number — this is usually a better fit than a plain function return for the actual transfer mechanic. Set the transfer destination to a real or simulated support number (e.g. a Twilio number you control, or just your own phone for the demo) and have the agent invoke that action when escalation conditions are met. Keep `log_fraud_report`/`escalate_to_agent` functions for logging/context-passing, but use Retell's call-transfer primitive for the actual handoff. Check Retell's current docs for the exact transfer-call setup, since this is a frequently updated feature.

---

## 4. Test internally before the demo

Run through each scenario in `docs/demo_call_scripts.md` — at minimum:
- Happy path lookup (script 1, CUST001)
- Eligible vs. ineligible eligibility check (scripts 2 & 3)
- An advance-EMI request that exceeds the allowed cap (script 6) — confirms the bot doesn't just blindly comply
- The "urgent / highest interest" pressure scenario (script 7) — confirms the responsible-lending guardrail holds
- The abusive-caller scenario (script 9) — confirms one warning, then escalation
- A failed-verification call (wrong DOB twice) — confirms the bot refuses to proceed without identity match

Watch Retell's call transcript/logs after each test call to see which functions were called, with what arguments, and what they returned — this is the fastest way to catch a prompt/function mismatch before the live demo.

---

## 5. Demo day flow (suggested order)

1. **Open with company context** (30 seconds): "MyShubhLife is an NBFC-backed fintech serving blue-collar/grey-collar workers in India — this bot handles their loan support calls."
2. **Script 1**: basic loan-amount lookup — show the JSON record on screen next to the live call to prove the answer is real, not scripted text-to-speech.
3. **Script 2 vs 3**: same intent ("can I get a new loan"), two different real outcomes (eligible+pre-approved vs. blocked by one-loan policy) — this demonstrates the bot is reasoning over actual account state, not giving a canned answer.
4. **Script 7**: the "urgent, give me the highest interest loan" pressure test — this is usually the single most convincing guardrail moment for a lending-compliance audience.
5. **Script 9**: abusive caller → one warning → escalation to a human agent — show the transfer happening live.
6. **Close with the eligibility/KYC and fraud-report scripts (10, 13)** if time allows, since they show breadth across compliance-sensitive categories.
7. Mention next steps: connecting to MyShubhLife's real loan management system in place of `customers.json`, adding call recording/QA, and load-testing concurrent calls before any production pilot.

---

## 6. Known POC limitations to disclose upfront (don't let these surprise a reviewer)

- **Data is 100% synthetic** — no real MyShubhLife customer data was used or seen.
- **Payments, SMS, and statements are simulated** (printed to a log, not actually sent) — wiring real payment gateway / SMS gateway integration is a follow-on workstream, not part of this POC.
- **Foreclosure fee math is a placeholder estimate** (2% of outstanding, min ₹250) — get MyShubhLife's actual foreclosure fee schedule before this goes anywhere near production.
- **Identity verification here is a simple attribute match** (DOB/name/Aadhaar-last-4 against a database field) — a production version should use a stronger method (OTP to registered mobile is the obvious one) before this is trusted with real financial data.
- **Language/voice coverage depends on Retell's current TTS/STT support** for Indian languages — confirm exact coverage in Retell's docs rather than assuming all of Hindi/Tamil/Kannada/Telugu/Malayalam/Bengali/Punjabi/Urdu/Marathi are equally well supported today.
- **Call transfer mechanics** should use Retell's native transfer-call feature in production, not just a function-call log.

---

## 7. Path from this POC to a real pilot

1. Replace `data/customers.json` + `server.py` with a real read-only API into MyShubhLife's loan management system (keep write actions — payments, KYC, mobile-number changes — happening only through verified, audited channels, never as a side-effect of an LLM function call without a human/OTP gate).
2. Add proper authentication on the webhook (Retell supports custom headers — use a shared secret or signed request, not an open endpoint).
3. Add real OTP-based identity verification (send OTP via SMS, verify via a function call) instead of attribute-matching.
4. Add call recording + a QA review queue for a sample of bot-handled calls, especially anything touching the guardrail categories (abusive callers, distress signals, eligibility decisions).
5. Add analytics: intent-resolution rate, escalation rate by reason, average handle time, customer satisfaction post-call.
6. Run a small live pilot (e.g. 1–2 employer-partner cohorts) before any wider rollout, with a clear rollback plan to all-human support if metrics dip.
7. Legal/compliance review specific to RBI's fair-practices and outsourcing/AI-in-lending guidance before any production deployment that can affect real credit decisions or collections communication — this POC does not constitute that review.

---

## 8. About MyShubhLife (for your own context, not just the bot's)

MyShubhLife (formerly Shubh Loans) is a Bengaluru-based NBFC-backed embedded finance platform, founded in 2016, serving the "Next Half Billion" — salaried blue-collar/grey-collar workers and gig workers who are largely outside the formal credit system. It lends through its NBFC entity (Ekagrata) and partners with employers (HRMS/payroll tie-ups) to enable salary-deduction repayment, which is a meaningfully different (and lower-risk) collections model than the typical app-based instant-loan NBFC that relies purely on bank-statement/NACH underwriting. Worth knowing before you pitch this: MyShubhLife was reported in 2024 to be in the process of being acquired by NBFC UGRO Capital — if this is still pending or has changed status, that's worth verifying directly with the company before finalizing any commercial proposal, since an ownership change could affect who you're actually contracting with.
