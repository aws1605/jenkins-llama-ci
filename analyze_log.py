#!/usr/bin/env python3
import requests, os, json, subprocess
from email.message import EmailMessage
import smtplib

# --------- Configuration ----------
OLLAMA_HOST = "http://localhost:11434"
MODEL = "llama3.2"
BUILD_LOG_PATH = "build.log"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USER = "your.email@gmail.com"        # <-- change
SMTP_APP_PASSWORD = "your_app_password"   # <-- change
EMAIL_TO = "developer.email@example.com"  # <-- change
# ----------------------------------

def read_build_log(path):
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def call_ollama_chat(messages):
    url = f"{OLLAMA_HOST}/api/chat"
    payload = {"model": MODEL, "messages": messages, "stream": False}
    resp = requests.post(url, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    if "choices" in data and len(data["choices"]) > 0:
        return data["choices"][0]["message"]["content"]
    if "output" in data:
        return data["output"]
    return str(data)

def analyze_log_with_ai(log_text):
    system = {"role": "system", "content": "You are an expert CI engineer. Analyze Jenkins build logs and identify errors, root cause, and concrete fix suggestions."}
    user = {"role": "user", "content": f"Here is the Jenkins build log:\n\n{log_text}\n\nPlease summarize the errors, root cause, and fixes."}
    return call_ollama_chat([system, user])

def send_email(subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL_TO

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.login(SMTP_USER, SMTP_APP_PASSWORD)
        smtp.send_message(msg)
        print("✅ Email sent to", EMAIL_TO)

def main():
    log_text = read_build_log(BUILD_LOG_PATH)
    if not log_text:
        print("No build log found.")
        return
    ai_reply = analyze_log_with_ai(log_text)
    print("AI summary:\n", ai_reply)
    if any(x in ai_reply.lower() for x in ["error", "fail", "traceback"]):
        send_email("Jenkins Build: Errors found — AI analysis", ai_reply)
    else:
        send_email("Jenkins Build: Passed — AI analysis", ai_reply)

if __name__ == "__main__":
    main()
