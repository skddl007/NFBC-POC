# MyShubhLife Voice Bot — local dev startup
# Run from project root: .\start-dev.ps1

$ProjectRoot = $PSScriptRoot
$FunctionsDir = Join-Path $ProjectRoot "functions"
$NgrokExe = Join-Path $ProjectRoot "tools\ngrok\ngrok.exe"

Write-Host "`n=== MyShubhLife Voice Bot — Dev Setup ===`n" -ForegroundColor Cyan

# 1. Flask backend
Write-Host "[1/2] Starting Flask backend on port 5000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$FunctionsDir'; python server.py"

Start-Sleep -Seconds 3
try {
    $health = Invoke-RestMethod -Uri "http://localhost:5000/health" -Method GET
    Write-Host "      Flask OK — $($health.customers_loaded) customers loaded" -ForegroundColor Green
} catch {
    Write-Host "      Flask not responding yet. Check the Flask terminal window." -ForegroundColor Red
}

# 2. Public tunnel
Write-Host "`n[2/2] Starting public tunnel..." -ForegroundColor Yellow

if (Test-Path $NgrokExe) {
    Write-Host "      Using ngrok (requires free authtoken — see below if it fails)" -ForegroundColor Gray
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "& '$NgrokExe' http 5000"
    Write-Host @"

      If ngrok shows ERR_NGROK_4018, run once:
        $NgrokExe config add-authtoken YOUR_TOKEN
      Get token: https://dashboard.ngrok.com/get-started/your-authtoken

      Copy the https://....ngrok-free.app URL from the ngrok window.
"@ -ForegroundColor Gray
} else {
    Write-Host "      Using localtunnel (no signup needed)" -ForegroundColor Gray
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "npx --yes localtunnel --port 5000"
    Write-Host "      Copy the https://....loca.lt URL from the tunnel window." -ForegroundColor Gray
}

Write-Host @"

=== Next: configure Retell ===
1. Paste prompts/retell_system_prompt.md into Retell General Prompt
2. Add all 11 custom functions from functions/retell_function_schemas.json
3. Set each function URL to:
     https://<YOUR-TUNNEL-URL>/functions/<function_name>

Functions:
  lookup_customer_by_mobile
  verify_identity
  get_loan_details
  get_payment_history
  check_loan_eligibility
  check_advance_payment_eligibility
  get_foreclosure_quote
  initiate_payment_link
  send_statement
  log_fraud_report
  escalate_to_agent

Test mobile: 9982385483 (Sandeep Kumar), DOB: 1988-04-12
"@ -ForegroundColor Cyan
