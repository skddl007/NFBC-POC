# Guardrails & Governance Summary — MyShubhLife Voice Bot POC

A one-page reference of every guardrail built into this bot, organized by risk category. Useful to hand to a compliance/risk reviewer separately from the full build guide.

## 1. Identity & privacy
| Guardrail | Mechanism |
|---|---|
| No financial data shared before identity confirmed | Two-step check: mobile lookup (`lookup_customer_by_mobile`) + secondary attribute match (`verify_identity`) |
| No third-party account access | Bot explicitly refuses to discuss anyone else's account, even if caller has some of their details |
| Failed verification → no guessing | Two failed attempts → escalate to human agent, never proceed on partial match |
| Never collect OTP/PIN/CVV/passwords | Hard rule in system prompt; bot stops the caller if they try to read one out |

## 2. Responsible lending
| Guardrail | Mechanism |
|---|---|
| Bot cannot approve/disburse loans | Only reports `check_loan_eligibility` results; explains app/agent is needed to actually proceed |
| Bot cannot change rate/tenure/EMI | Any negotiation request → offer to flag for human review, never improvise terms |
| Urgency/pressure does not bypass eligibility | "Urgent, give me the highest amount" still routes through the real eligibility function; bot does not chase the costliest product |
| One-loan-at-a-time policy enforced | `check_loan_eligibility` returns real `ineligible` state for customers with an active loan; bot states this plainly |
| Advance/partial EMI payments capped per customer | `check_advance_payment_eligibility` enforces `max_advance_emis_allowed`; bot does not exceed it even if asked |
| No encouragement of debt cycling | If caller implies borrowing to repay another debt, bot flags it gently rather than processing it as routine |
| Settlement/restructuring never bot-decided | Only mentioned if `settlement_offer_eligible` is true, and always requires human/specialist follow-up |

## 3. Tone & difficult-caller handling
| Caller behavior | Bot response pattern |
|---|---|
| Anxious / high-pitch / fast | Slow down, brief acknowledgment, then facts — does not mirror urgency |
| Soft-spoken / elderly | Speaks clearly, checks audibility, repeats numbers without impatience |
| Confused / first-time | Plain language, checks understanding before moving on |
| Frustrated but not abusive | Stays calm, acknowledges frustration once, redirects to resolution |
| Abusive / profanity / threats | One calm warning → continued abuse → transfer to human agent. Never argues back. |
| Emotional distress about debt | Validates without over-promising; offers human/specialist escalation if restructuring is genuinely available |
| Self-harm / suicide signal | Immediately stops account troubleshooting, expresses concern, surfaces a crisis helpline (KIRAN: 1800-599-0019), transfers to a human agent |

## 4. Fraud & security
| Guardrail | Mechanism |
|---|---|
| Fraud/phishing reports taken seriously immediately | Bot confirms MyShubhLife never asks for OTP/PIN over a call, logs via `log_fraud_report`, escalates |
| Sensitive account changes never self-served | Mobile number / bank account / NACH mandate changes always redirected to app (OTP-gated) or human agent |

## 5. Escalation triggers (full list)
Escalate to a human agent whenever:
1. Identity verification fails twice
2. Caller explicitly asks for a human
3. Sensitive account change requested
4. Caller is abusive after one warning
5. Mental health / self-harm risk signals appear
6. Fraud/phishing report is made
7. Caller wants to negotiate rate, restructure, or get a fee waiver
8. Request is outside the bot's defined scope (legal, regulatory, media, employer disputes)
9. A function call fails or returns unusable data
10. Bot is not confident its answer is correct

## 6. Data & POC-specific disclosures
- All 20 customer records are synthetic, generated for this POC — no real MyShubhLife customer data is used.
- Payment links, SMS, and statements are simulated (logged, not actually dispatched).
- This POC has not undergone a formal RBI fair-practices / outsourcing-in-AI compliance review — required before any production deployment that touches real credit decisions or collections communication.
