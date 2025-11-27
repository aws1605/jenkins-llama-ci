#!/usr/bin/env python3
"""
analyze_log.py

- Reads build.log in current working directory
- Calls local Ollama REST API to analyze build log using llama3.2:latest
- Sends an email with AI analysis (or with an Ollama error / missing-log notice)
- Prints clear debug output for Jenkins console
"""""""""

import os
import json
import requests
import smtplib
from email.message import EmailMessage
import traceback
from typing import Optional

# ----------------- CONFIGURATION (EDIT THESE) ------------------------
OLLAMA_HOST = "http://localhost:11434"      # Ollama REST API host
MODEL = "llama3.2:latest"                   # Exact model name from `ollama list`
BUILD_LOG_PATH = "build.log"

# SMTP / Gmail - REPLACE these with your actual values
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USER = "awsawsaws1605@gmail.com"          # <-- REPLACE: your gmail id
SMTP_APP_PASSWORD = "htvsybrqqlxvfjta"     # <-- REPLACE: Gmail App Password without any space (16 chars)
EMAIL_TO = "awsawsaws1605@gmail.com"      # <-- REPLACE: where you want to receive reports
# ----------------------------------------------------------------

# Small utility: safe print wrapper for Jenkins console
def log(*args, **kwargs):
    print(*args, **kwargs, flush=True)

def read_build_log(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def call_ollama_chat(messages) -> str:
    """
    Call Ollama /api/chat and return the assistant content or raise.
    This function includes debug prints and helpful error text on failure.
    """
    url = f"{OLLAMA_HOST}/api/chat"
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False
    }
    headers = {"Content-Type": "application/json"}

    try:
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=120)
        log(f"DEBUG: Ollama HTTP status: {resp.status_code}")
        if resp.status_code != 200:
            # Print body for debugging
            log("DEBUG: Ollama response body:", resp.text)
        resp.raise_for_status()
        data = resp.json()
        # Try common response shapes
        if isinstance(data, dict):
            # Ollama newer shape: choices -> [ { message: { content: ... } } ]
            if "choices" in data and isinstance(data["choices"], list) and len(data["choices"]) > 0:
                try:
                    return data["choices"][0]["message"]["content"]
                except Exception:
                    pass
            # older or alternate: data.get("output") or data.get("message")
            if "output" in data:
                return data["output"]
            if "message" in data and isinstance(data["message"], dict):
                return data["message"].get("content", str(data))
        # fallback: try direct text
        return str(data)
    except requests.exceptions.RequestException as e:
        # Return an explicit error string for caller to include in email
        errtxt = f"Ollama request failed: {e}"
        log("ERROR:", errtxt)
        # include traceback for Jenkins console
        log(traceback.format_exc())
        raise RuntimeError(errtxt) from e

def analyze_log_with_ai(log_text: str) -> str:
    """
    Build a structured prompt for the CI engineer assistant.
    Returns the AI text (or raises if Ollama call fails).
    """
    system_msg = {
        "role": "system",
        "content": (
            "You are an expert CI engineer. Analyze the Jenkins build log given by the user. "
            "Provide a short summary of the failure (or success), the probable root cause, "
            "and exact code changes or commands to fix it if applicable. If no error is found, "
            "reply that the build passed."
        )
    }
    user_msg = {
        "role": "user",
        "content": f"Jenkins build log:\n\n{log_text}\n\nPlease respond with a concise summary, root cause, and concrete fixes (if any)."
    }
    return call_ollama_chat([system_msg, user_msg])

def send_email(subject: str, body: str) -> None:
    """
    Send an email using SMTP_SSL.
    """
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL_TO
    # keep body shorter if very large logs
    if len(body) > 15000:
        body = body[:15000] + "\n\n[Truncated — full log available in Jenkins workspace]"
    msg.set_content(body)

    log("DEBUG: Attempting to connect to SMTP server...")
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30) as smtp:
            smtp.login(SMTP_USER, SMTP_APP_PASSWORD)
            smtp.send_message(msg)
        log(f"✅ Email sent to {EMAIL_TO}")
    except Exception as e:
        log("❌ Failed to send email:", e)
        log(traceback.format_exc())
        raise

def main():
    log("=== DEBUG: Starting analyze_log.py ===")
    log("Working dir:", os.getcwd())
    log("Workspace files:", os.listdir("."))

    # read build log
    log_text = read_build_log(BUILD_LOG_PATH)
    if not log_text:
        # If no build log, still send a notification so you know something happened
        subject = "Jenkins Build: No build.log found"
        body = (
            "The Jenkins job ran but no build.log file was present in the workspace.\n\n"
            "Current files: " + ", ".join(os.listdir(".")) + "\n\n"
            "If tests ran, ensure pytest output is redirected to build.log in the Jenkinsfile, e.g.:\n"
            "pytest ... > build.log 2>&1 || true\n"
        )
        log("No build.log found — sending notification email.")
        try:
            send_email(subject, body)
        except Exception:
            log("Email send failed for missing log. See above for errors.")
        return

    # call AI (wrap in try to still send email if Ollama fails)
    ai_reply = None
    try:
        ai_reply = analyze_log_with_ai(log_text)
    except Exception as e:
        # Ollama failed — send email anyway with the error info and the raw log
        subject = "Jenkins Build: Ollama analysis failed — see raw build log"
        body = (
            "Ollama (local LLaMA server) failed to analyze the build log.\n\n"
            f"Error: {e}\n\n"
            "Full Jenkins build.log follows:\n\n" + log_text
        )
        log("Ollama failed. Sending email containing the raw build.log and error.")
        try:
            send_email(subject, body)
        except Exception:
            log("Email sending failed while reporting Ollama failure.")
        return

    # if we have an AI reply, choose subject based on content
    subj = "Jenkins Build: Passed — AI analysis"
    lower = ai_reply.lower()
    if any(token in lower for token in ["error", "fail", "traceback", "exception", "failed"]):
        subj = "Jenkins Build: Errors found — AI analysis"

    # Compose email body
    body = f"AI analysis (model: {MODEL}):\n\n{ai_reply}\n\n\n(full build.log below)\n\n{log_text}"
    try:
        send_email(subj, body)
    except Exception:
        log("Final email send failed. See logs above for SMTP error.")

if __name__ == "__main__":
    main()
