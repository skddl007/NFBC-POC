"""
MyShubhLife Voice Bot — Backend Stub for Retell Custom Functions
==================================================================
Minimal Flask server implementing every function defined in
functions/retell_function_schemas.json, backed by data/customers.json.

THIS IS A POC STUB, NOT PRODUCTION CODE:
- No real database, no auth on the webhook beyond an optional shared secret.
- Payment links / SMS / fraud logs are simulated (printed + returned), not actually sent.
- In a real build, replace the JSON file with your core loan management
  system / CRM via proper APIs, and put this behind authentication
  (Retell supports custom headers for webhook auth).

HOW TO RUN LOCALLY:
    pip install flask --break-system-packages
    python3 server.py
    # Server runs on http://0.0.0.0:5000

HOW TO EXPOSE FOR RETELL (pick one):
    - ngrok http 5000          (fastest for a live demo)
    - Deploy to Render/Railway/Fly.io for a stable URL
    - Then set each Retell Custom Function's "URL" to:
        https://<your-public-url>/functions/<function_name>

Each Retell custom function should be configured to POST a JSON body
shaped like: {"args": {...the parameters...}}
This stub also accepts the parameters directly at the top level, to be
tolerant of Retell's exact wire format (check current Retell docs —
format has changed across versions).
"""

import json
import os
import random
import string
from datetime import datetime
from flask import Flask, request, jsonify

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(APP_DIR, "..", "data", "customers.json")

app = Flask(__name__)

with open(DATA_PATH, "r", encoding="utf-8") as f:
    DB = json.load(f)

def normalize_mobile(value):
    """Reduce any mobile format (+91, spaces, dashes, etc.) to its last 10 digits."""
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return digits[-10:]


CUSTOMERS_BY_ID = {c["id"]: c for c in DB["customers"]}

# Index by normalized mobile AND alt_mobile so lookups match regardless of how
# the number is stored or how the caller's number arrives (+91, spaces, etc.).
CUSTOMERS_BY_MOBILE = {}
for _c in DB["customers"]:
    for _num in (_c.get("mobile"), _c.get("alt_mobile")):
        _norm = normalize_mobile(_num)
        if _norm:
            CUSTOMERS_BY_MOBILE.setdefault(_norm, _c)

FRAUD_LOG = []  # in-memory only, resets on restart — fine for a POC


def get_args():
    """Tolerant extraction of function arguments from Retell's webhook payload."""
    body = request.get_json(silent=True) or {}
    if "args" in body and isinstance(body["args"], dict):
        return body["args"]
    return body


def find_loan(customer, loan_id=None):
    loans = customer.get("loans", [])
    if not loans:
        return None
    if loan_id:
        for l in loans:
            if l["loan_id"] == loan_id:
                return l
        return None
    active = [l for l in loans if l["status"] in ("active", "closing_this_cycle")]
    if active:
        return active[0]
    closed = [l for l in loans if l["status"] == "closed"]
    if closed:
        return sorted(closed, key=lambda x: x.get("closure_date", ""), reverse=True)[0]
    return loans[-1]


def rupee(amount):
    return f"₹{amount:,.0f}"


@app.route("/functions/lookup_customer_by_mobile", methods=["POST"])
def lookup_customer_by_mobile():
    args = get_args()
    mobile = normalize_mobile(args.get("mobile_number"))
    customer = CUSTOMERS_BY_MOBILE.get(mobile)
    if not customer:
        return jsonify({
            "found": False,
            "message": "No account found for this mobile number. Ask the caller to double-check the number."
        })
    return jsonify({
        "found": True,
        "customer_id": customer["id"],
        "name": customer["name"],
        "preferred_language": customer["preferred_language"],
        "city": customer["city"],
        "kyc_status": customer["kyc_status"],
        "verification_required": True,
        "message": "Account found. Verify identity before sharing any financial details."
    })


@app.route("/functions/verify_identity", methods=["POST"])
def verify_identity():
    args = get_args()
    customer_id = args.get("customer_id")
    vtype = args.get("verification_type")
    vvalue = (args.get("verification_value") or "").strip().lower()

    customer = CUSTOMERS_BY_ID.get(customer_id)
    if not customer:
        return jsonify({"verified": False, "message": "Customer ID not found."})

    if vtype == "full_name":
        match = vvalue in customer["name"].lower() or customer["name"].lower() in vvalue
    elif vtype == "date_of_birth":
        match = vvalue.replace("/", "-") == customer["dob"]
    elif vtype == "aadhaar_last4":
        match = vvalue[-4:] == customer["aadhaar_last4"]
    else:
        match = False

    return jsonify({
        "verified": bool(match),
        "message": "Identity verified." if match else "Verification value did not match. Try a different identifier or attempt once more before escalating."
    })


@app.route("/functions/get_loan_details", methods=["POST"])
def get_loan_details():
    args = get_args()
    customer = CUSTOMERS_BY_ID.get(args.get("customer_id"))
    if not customer:
        return jsonify({"found": False, "message": "Customer not found."})

    loan = find_loan(customer, args.get("loan_id"))
    if not loan:
        return jsonify({"found": False, "message": "No loans on record for this customer."})

    return jsonify({
        "found": True,
        "loan_id": loan["loan_id"],
        "purpose": loan["purpose"],
        "principal_amount": loan["principal"],
        "principal_amount_spoken": rupee(loan["principal"]),
        "interest_rate_pa": loan["interest_rate"],
        "tenure_months": loan["tenure_months"],
        "emi_amount": loan["emi"],
        "emi_amount_spoken": rupee(loan["emi"]),
        "status": loan["status"],
        "paid_emis": loan["paid_emis"],
        "remaining_emis": loan["tenure_months"] - loan["paid_emis"],
        "outstanding_amount": loan["outstanding"],
        "outstanding_amount_spoken": rupee(loan["outstanding"]),
        "next_due_date": loan.get("next_due_date"),
        "next_emi_amount": loan.get("next_emi_amount"),
        "overdue_days": loan.get("overdue_days", 0),
        "late_fee_pending": loan.get("late_fee_pending", 0),
        "nach_bounce_count": loan.get("nach_bounce_count", 0),
        "disbursed_date": loan.get("disbursed_date"),
        "closure_date": loan.get("closure_date")
    })


@app.route("/functions/get_payment_history", methods=["POST"])
def get_payment_history():
    args = get_args()
    customer = CUSTOMERS_BY_ID.get(args.get("customer_id"))
    if not customer:
        return jsonify({"found": False, "message": "Customer not found."})

    loan_id = args.get("loan_id")
    if loan_id:
        loan = find_loan(customer, loan_id)
        if not loan:
            return jsonify({"found": False, "message": "Loan not found."})
        amount_paid = loan["emi"] * loan["paid_emis"] + loan.get("processing_fee_paid", 0)
        return jsonify({
            "found": True,
            "loan_id": loan["loan_id"],
            "paid_emis": loan["paid_emis"],
            "tenure_months": loan["tenure_months"],
            "amount_paid_this_loan": amount_paid,
            "amount_paid_this_loan_spoken": rupee(amount_paid),
            "last_payment_date": loan.get("last_payment_date"),
            "last_payment_amount": loan.get("last_payment_amount"),
            "payment_history_rating": customer["payment_history"]
        })

    return jsonify({
        "found": True,
        "total_paid_to_date": customer["total_paid_to_date"],
        "total_paid_to_date_spoken": rupee(customer["total_paid_to_date"]),
        "payment_history_rating": customer["payment_history"],
        "nach_status": customer["nach_status"],
        "number_of_loans": len(customer["loans"])
    })


@app.route("/functions/check_loan_eligibility", methods=["POST"])
def check_loan_eligibility():
    args = get_args()
    customer = CUSTOMERS_BY_ID.get(args.get("customer_id"))
    if not customer:
        return jsonify({"found": False, "message": "Customer not found."})

    result = {
        "found": True,
        "eligible": customer["eligible_next_loan"],
        "max_eligible_amount": customer.get("max_eligible_amount", 0),
        "max_eligible_amount_spoken": rupee(customer.get("max_eligible_amount", 0)),
        "kyc_status": customer["kyc_status"]
    }
    if not customer["eligible_next_loan"]:
        result["ineligibility_reason"] = customer.get("ineligibility_reason", "Not currently eligible.")
    if customer.get("pre_approved"):
        result["pre_approved"] = True
        result["pre_approved_amount"] = customer["pre_approved_amount"]
        result["pre_approved_amount_spoken"] = rupee(customer["pre_approved_amount"])
        result["pre_approved_rate_pa"] = customer["pre_approved_rate"]
    else:
        result["pre_approved"] = False
    return jsonify(result)


@app.route("/functions/check_advance_payment_eligibility", methods=["POST"])
def check_advance_payment_eligibility():
    args = get_args()
    customer = CUSTOMERS_BY_ID.get(args.get("customer_id"))
    if not customer:
        return jsonify({"found": False, "message": "Customer not found."})

    loan = find_loan(customer, args.get("loan_id"))
    if not loan:
        return jsonify({"found": False, "message": "No active loan found."})

    requested = int(args.get("requested_emi_count", 1))
    allowed = customer.get("advance_emi_allowed", False)
    max_allowed = customer.get("max_advance_emis_allowed", 0)
    remaining_emis = loan["tenure_months"] - loan["paid_emis"]

    can_fulfill = allowed and requested <= max_allowed and requested <= remaining_emis
    amount = loan["emi"] * min(requested, max_allowed) if allowed else 0

    return jsonify({
        "found": True,
        "loan_id": loan["loan_id"],
        "advance_payment_allowed": allowed,
        "max_advance_emis_allowed": max_allowed,
        "requested_emi_count": requested,
        "can_fulfill_full_request": can_fulfill,
        "payable_amount_for_max_allowed": amount,
        "payable_amount_for_max_allowed_spoken": rupee(amount),
        "message": (
            "Customer can pay this many advance EMIs as requested."
            if can_fulfill else
            f"Customer is only permitted up to {max_allowed} advance EMI(s) this cycle, or advance payment isn't available — offer that amount instead, or transfer for a special request."
        )
    })


@app.route("/functions/get_foreclosure_quote", methods=["POST"])
def get_foreclosure_quote():
    args = get_args()
    customer = CUSTOMERS_BY_ID.get(args.get("customer_id"))
    if not customer:
        return jsonify({"found": False, "message": "Customer not found."})

    loan = find_loan(customer, args.get("loan_id"))
    if not loan or loan["status"] not in ("active", "closing_this_cycle"):
        return jsonify({"found": False, "message": "No active loan eligible for foreclosure."})

    outstanding_principal_est = loan["outstanding"]
    # Simple flat foreclosure fee assumption for POC purposes: 2% of outstanding, min ₹250
    foreclosure_fee = max(round(outstanding_principal_est * 0.02), 250)
    total_payable = outstanding_principal_est + foreclosure_fee

    return jsonify({
        "found": True,
        "loan_id": loan["loan_id"],
        "outstanding_amount": outstanding_principal_est,
        "foreclosure_fee": foreclosure_fee,
        "total_payable_today": total_payable,
        "total_payable_today_spoken": rupee(total_payable),
        "note": "Foreclosure fee is an indicative POC estimate (2% of outstanding, min ₹250). Confirm exact figure from the official schedule before quoting in production."
    })


@app.route("/functions/initiate_payment_link", methods=["POST"])
def initiate_payment_link():
    args = get_args()
    customer = CUSTOMERS_BY_ID.get(args.get("customer_id"))
    if not customer:
        return jsonify({"success": False, "message": "Customer not found."})

    link_id = "PAY" + "".join(random.choices(string.digits, k=8))
    simulated_link = f"https://pay.myshubhlife.com/l/{link_id}"

    print(f"[SIMULATED SMS] To {customer['mobile']}: Pay {rupee(args.get('amount', 0))} "
          f"({args.get('payment_type')}) for loan {args.get('loan_id')} here: {simulated_link}")

    return jsonify({
        "success": True,
        "payment_link": simulated_link,
        "amount": args.get("amount"),
        "sent_to_mobile": customer["mobile"],
        "message": "Payment link generated and sent via SMS (simulated in this POC)."
    })


@app.route("/functions/send_statement", methods=["POST"])
def send_statement():
    args = get_args()
    customer = CUSTOMERS_BY_ID.get(args.get("customer_id"))
    if not customer:
        return jsonify({"success": False, "message": "Customer not found."})

    method = args.get("delivery_method", "sms")
    print(f"[SIMULATED {method.upper()}] Statement sent to {customer['name']} "
          f"({customer['mobile']}) for loan {args.get('loan_id', 'ALL')}")

    return jsonify({
        "success": True,
        "delivery_method": method,
        "message": f"Statement dispatched via {method} (simulated in this POC)."
    })


@app.route("/functions/log_fraud_report", methods=["POST"])
def log_fraud_report():
    args = get_args()
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "customer_id": args.get("customer_id"),
        "description": args.get("description"),
        "reported_number": args.get("reported_number")
    }
    FRAUD_LOG.append(entry)
    print(f"[FRAUD LOG] {entry}")
    return jsonify({"logged": True, "case_reference": f"FR{len(FRAUD_LOG):05d}"})


@app.route("/functions/escalate_to_agent", methods=["POST"])
def escalate_to_agent():
    args = get_args()
    print(f"[ESCALATION] customer={args.get('customer_id')} reason={args.get('reason')} "
          f"summary={args.get('context_summary')}")
    # In a real Retell setup, escalation is usually wired as a "transfer_call" action
    # at the agent level (see docs/build_guide.md) rather than a plain function return.
    return jsonify({
        "escalated": True,
        "transfer_number": "+916397039765",
        "agent_name": "human agent",
        "message": "Call is being transferred to a human agent."
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "customers_loaded": len(CUSTOMERS_BY_ID)})


if __name__ == "__main__":
    print(f"Loaded {len(CUSTOMERS_BY_ID)} synthetic customers from {DATA_PATH}")
    app.run(host="0.0.0.0", port=5000, debug=True)
