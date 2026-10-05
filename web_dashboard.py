from __future__ import annotations

import json
import mimetypes
import argparse
import os
import threading
import time
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from twilio import TwilioService, build_emergency_sms, build_voice_message


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

DRIVER_RESPONSE_SECONDS = 30
CONTACT_ACK_SECONDS = 15


def now_stamp() -> str:
    return datetime.now().strftime("%d-%m-%Y  %I:%M:%S %p")


def log_stamp() -> str:
    return datetime.now().strftime("%I:%M:%S %p")


@dataclass
class Contact:
    name: str
    number: str
    role: str
    sms_status: str = "Standby"
    call_status: str = "Standby"

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "number": self.number,
            "role": self.role,
            "sms_status": self.sms_status,
            "call_status": self.call_status,
        }


@dataclass
class DashboardState:
    mode: str = "normal"
    vehicle_number: str = "TN 01 AB 1234"
    location_text: str = "11.0168, 76.9558  |  Coimbatore Bypass"
    event_time: str = "--:--"
    system_status: str = "Monitoring Normal"
    alarm_state: str = "Silent"
    dispatch_state: str = "Standby"
    active_timer: str = "--:--"
    banner: str = "System is monitoring continuously. No accident event is active."
    current_stage: str = "Continuous monitoring active"
    driver_response: str = "Waiting for normal operation"
    recipients_summary: str = "No alerts sent yet"
    demo_mode: bool = True
    twilio_ready: bool = False
    run_id: int = 0
    logs: list[dict[str, str]] = field(default_factory=list)
    contacts: list[Contact] = field(default_factory=list)


class AccidentDashboardController:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.twilio_service = TwilioService()
        self.state = DashboardState(contacts=self._build_contacts())
        self._refresh_twilio_ready()
        self.state.demo_mode = self._initial_demo_mode()
        mode_label = "demo" if self.state.demo_mode else "real Twilio"
        self._append_log(f"Dashboard server initialized. Notification mode is {mode_label}.", "success")

    def _initial_demo_mode(self) -> bool:
        configured = os.getenv("DASHBOARD_DEMO_MODE", "").strip().lower()
        if configured in {"1", "true", "yes", "on"}:
            return True
        if configured in {"0", "false", "no", "off"}:
            return False
        return not self.state.twilio_ready

    def _build_contacts(self) -> list[Contact]:
        seeded_numbers = [
            "+919715252055",
            "+919994138347",
            "+916381681459",
            "+918903971809",
            "+917708009353",
        ]
        contacts = [
            Contact(f"Emergency Contact {index + 1}", number, "Family")
            for index, number in enumerate(seeded_numbers)
        ]
        contacts.extend(
            [
                Contact("Ambulance Service", "+91XXXXXXXX11", "Responder"),
                Contact("Police Control Room", "+91XXXXXXXX12", "Responder"),
                Contact("Nearest Hospital", "+91XXXXXXXX13", "Responder"),
            ]
        )
        return contacts

    def _refresh_twilio_ready(self) -> None:
        issues = self.twilio_service.validate_configuration(self.state.contacts[0].number)
        self.state.twilio_ready = not issues

    def _append_log(self, message: str, level: str = "info") -> None:
        self.state.logs.append({"time": log_stamp(), "message": message, "level": level})
        self.state.logs = self.state.logs[-120:]

    def _bump_run(self) -> int:
        self.state.run_id += 1
        return self.state.run_id

    def _timer_text(self, seconds: int) -> str:
        minutes, secs = divmod(seconds, 60)
        return f"{minutes:02d}:{secs:02d}"

    def _recipients_label(self, prefix: str = "Recipients") -> str:
        family_count = sum(1 for contact in self.state.contacts if contact.role == "Family")
        responder_count = len(self.state.contacts) - family_count
        return f"{prefix}: {family_count} emergency contacts + {responder_count} responders"

    def _reset_contact_status(self) -> None:
        for contact in self.state.contacts:
            contact.sms_status = "Standby"
            contact.call_status = "Standby"

    def get_state(self) -> dict[str, Any]:
        with self.lock:
            self._refresh_twilio_ready()
            return {
                "mode": self.state.mode,
                "vehicle_number": self.state.vehicle_number,
                "location_text": self.state.location_text,
                "event_time": self.state.event_time,
                "system_status": self.state.system_status,
                "alarm_state": self.state.alarm_state,
                "dispatch_state": self.state.dispatch_state,
                "active_timer": self.state.active_timer,
                "banner": self.state.banner,
                "current_stage": self.state.current_stage,
                "driver_response": self.state.driver_response,
                "recipients_summary": self.state.recipients_summary,
                "demo_mode": self.state.demo_mode,
                "twilio_ready": self.state.twilio_ready,
                "contacts": [contact.to_dict() for contact in self.state.contacts],
                "logs": list(self.state.logs),
            }

    def update_settings(self, payload: dict[str, Any]) -> dict[str, str]:
        with self.lock:
            vehicle_number = str(payload.get("vehicle_number", "")).strip()
            location_text = str(payload.get("location_text", "")).strip()
            demo_mode = payload.get("demo_mode")
            if vehicle_number:
                self.state.vehicle_number = vehicle_number[:40]
            if location_text:
                self.state.location_text = location_text[:120]
            if isinstance(demo_mode, bool):
                self.state.demo_mode = demo_mode
                mode_label = "demo" if demo_mode else "real Twilio"
                self._append_log(f"Notification mode changed to {mode_label}.", "info")
            self._refresh_twilio_ready()
            self._append_log("Vehicle and dashboard settings updated.", "success")
        return {"ok": "true"}

    def update_contact(self, payload: dict[str, Any]) -> dict[str, str]:
        index = int(payload.get("index", -1))
        name = str(payload.get("name", "")).strip()
        number = str(payload.get("number", "")).strip()
        with self.lock:
            if index < 0 or index >= len(self.state.contacts):
                return {"ok": "false", "error": "Invalid contact index."}
            if name:
                self.state.contacts[index].name = name[:48]
            if number:
                self.state.contacts[index].number = number[:24]
            self._refresh_twilio_ready()
            self._append_log(f"Contact {index + 1} updated.", "success")
        return {"ok": "true"}

    def reset(self) -> None:
        with self.lock:
            self._bump_run()
            self.state.mode = "normal"
            self.state.event_time = "--:--"
            self.state.system_status = "Monitoring Normal"
            self.state.alarm_state = "Silent"
            self.state.dispatch_state = "Standby"
            self.state.active_timer = "--:--"
            self.state.banner = "System is monitoring continuously. No accident event is active."
            self.state.current_stage = "Continuous monitoring active"
            self.state.driver_response = "Waiting for normal operation"
            self.state.recipients_summary = "No alerts sent yet"
            self._reset_contact_status()
            self._append_log("System reset completed. Dashboard returned to normal monitoring mode.", "success")

    def simulate_accident(self) -> None:
        with self.lock:
            run_id = self._bump_run()
            self.state.mode = "driver_wait"
            self.state.event_time = now_stamp()
            self.state.system_status = "Accident Detected"
            self.state.alarm_state = "Alarm Triggered"
            self.state.dispatch_state = "Waiting For Driver"
            self.state.current_stage = "Accident detected, buzzer alarm started"
            self.state.driver_response = "Driver must respond within 30 seconds"
            self.state.recipients_summary = self._recipients_label()
            self.state.banner = "Accident detected. Waiting 30 seconds for driver response before sending alerts."
            self._reset_contact_status()
            self._append_log("Accident sensor detected a collision. Emergency mode activated.", "danger")
            self._append_log("Alarm, buzzer, and dashboard warning indicators turned on.", "warning")
        threading.Thread(target=self._driver_countdown, args=(run_id,), daemon=True).start()

    def driver_responded(self) -> None:
        with self.lock:
            if self.state.mode != "driver_wait":
                self._append_log("Driver response was received outside the active timer window.", "info")
                return
            self._bump_run()
            self.state.mode = "resolved"
            self.state.system_status = "Driver Responded"
            self.state.alarm_state = "Alarm Stopped"
            self.state.dispatch_state = "No Alerts Sent"
            self.state.active_timer = "Resolved"
            self.state.current_stage = "Emergency stopped after driver response"
            self.state.driver_response = "Driver confirmed safe / conscious"
            self.state.recipients_summary = "Emergency messages cancelled"
            self.state.banner = "Driver responded within the allowed time. Emergency notification was cancelled."
            self._append_log("Driver responded within the response window.", "success")

    def cancel_false_alarm(self) -> None:
        with self.lock:
            self._bump_run()
            self.state.mode = "resolved"
            self.state.system_status = "False Alarm Cancelled"
            self.state.alarm_state = "Alarm Stopped"
            self.state.dispatch_state = "Escalation Cancelled"
            self.state.active_timer = "Cancelled"
            self.state.current_stage = "Emergency workflow stopped manually"
            self.state.driver_response = "False alarm marked by user"
            self.state.recipients_summary = "No further alerts will be sent"
            self.state.banner = "False alarm cancelled. Pending messages, calls, and escalation timers were stopped."
            self._append_log("User cancelled the alert as a false alarm.", "success")

    def call_contacts_now(self) -> None:
        with self.lock:
            run_id = self._bump_run()
            self.state.event_time = now_stamp()
            self._append_log("Manual contact call requested. Escalating directly to phone calls.", "warning")
        threading.Thread(target=self._begin_auto_calls, args=(run_id, True), daemon=True).start()

    def send_sms_now(self) -> None:
        with self.lock:
            run_id = self._bump_run()
            self.state.event_time = now_stamp()
            self.state.system_status = "Manual SMS Alert"
            self.state.alarm_state = "SMS Dispatch"
            self.state.dispatch_state = "Sending SMS Alerts"
            self.state.active_timer = "Sending"
            self.state.current_stage = "Manual emergency SMS dispatch requested"
            self.state.driver_response = "Manual alert sent from console"
            self.state.recipients_summary = self._recipients_label()
            self.state.banner = "Manual emergency SMS dispatch is active."
            self._reset_contact_status()
            self._append_log("Manual SMS alert button pressed. Sending emergency messages now.", "warning")
        threading.Thread(target=self._begin_message_dispatch, args=(run_id, False), daemon=True).start()

    def _driver_countdown(self, run_id: int) -> None:
        for seconds in range(DRIVER_RESPONSE_SECONDS, -1, -1):
            with self.lock:
                if run_id != self.state.run_id or self.state.mode != "driver_wait":
                    return
                self.state.active_timer = self._timer_text(seconds)
                if seconds in {20, 10, 5}:
                    self._append_log(f"{seconds} seconds remaining for driver acknowledgement.", "warning")
                if seconds == 0:
                    self._append_log("No driver response received within 30 seconds.", "danger")
                    break
            time.sleep(1)
        self._begin_message_dispatch(run_id)

    def _begin_message_dispatch(self, run_id: int, start_ack_timer: bool = True) -> None:
        with self.lock:
            if run_id != self.state.run_id:
                return
            self.state.mode = "message_dispatch"
            self.state.dispatch_state = "Sending SMS Alerts"
            self.state.alarm_state = "Alarm Active"
            self.state.current_stage = "Sending emergency SMS alerts automatically"
            self.state.driver_response = "Driver did not respond"
            self.state.banner = "Driver did not respond. Emergency messages are being sent automatically."
        for index, contact in enumerate(self.state.contacts):
            with self.lock:
                if run_id != self.state.run_id:
                    return
                contact.sms_status = "Sending"
                self._append_log(f"Dispatching SMS alert to {contact.name}.", "danger")
            result = self._send_sms(contact)
            with self.lock:
                if run_id != self.state.run_id:
                    return
                contact.sms_status = "Demo Sent" if result.get("status") == "demo" else ("Sent" if result["ok"] else "Blocked")
                self._log_delivery_result("SMS", contact.name, result)
            time.sleep(0.65 if index < len(self.state.contacts) - 1 else 0)
        if not start_ack_timer:
            with self.lock:
                if run_id != self.state.run_id:
                    return
                self.state.mode = "completed"
                self.state.system_status = "SMS Dispatch Completed"
                self.state.alarm_state = "SMS Sent"
                self.state.dispatch_state = "SMS Alerts Sent"
                self.state.active_timer = "Completed"
                self.state.current_stage = "Manual SMS dispatch completed"
                self.state.recipients_summary = "Emergency SMS alerts sent to saved contacts"
                self.state.banner = "Manual emergency SMS dispatch completed."
                self._append_log("Manual SMS dispatch completed.", "success")
            return
        self._contact_ack_countdown(run_id)

    def _contact_ack_countdown(self, run_id: int) -> None:
        with self.lock:
            if run_id != self.state.run_id:
                return
            self.state.mode = "contact_wait"
            self.state.dispatch_state = "Waiting For Acknowledgement"
            self.state.current_stage = "Messages sent, waiting for acknowledgement"
            self.state.banner = "Emergency SMS alerts were sent. Automatic calling starts if nobody acknowledges."
            self._append_log("Acknowledgement timer started before automatic call escalation.", "info")
        for seconds in range(CONTACT_ACK_SECONDS, -1, -1):
            with self.lock:
                if run_id != self.state.run_id or self.state.mode != "contact_wait":
                    return
                self.state.active_timer = self._timer_text(seconds)
                if seconds in {10, 5}:
                    self._append_log(f"{seconds} seconds remaining for contact acknowledgement.", "warning")
                if seconds == 0:
                    self._append_log("No acknowledgement received for the emergency message alerts.", "danger")
                    break
            time.sleep(1)
        self._begin_auto_calls(run_id)

    def _begin_auto_calls(self, run_id: int, manual_trigger: bool = False) -> None:
        with self.lock:
            if run_id != self.state.run_id:
                return
            self.state.mode = "auto_calling"
            self.state.system_status = "Calling Contacts" if manual_trigger else "Accident Confirmed"
            self.state.alarm_state = "Call Escalation Active"
            self.state.dispatch_state = "Automatic Calling"
            self.state.active_timer = "Calling"
            self.state.current_stage = "Calling emergency responders automatically"
            self.state.driver_response = "Manual direct call requested" if manual_trigger else "No response from driver"
            self.state.recipients_summary = self._recipients_label(prefix="Calling")
            self.state.banner = "The system is now calling responders immediately."
        for index, contact in enumerate(self.state.contacts):
            with self.lock:
                if run_id != self.state.run_id:
                    return
                contact.call_status = "Calling"
                self._append_log(f"Starting automatic call to {contact.name}.", "danger")
            result = self._make_call(contact)
            with self.lock:
                if run_id != self.state.run_id:
                    return
                contact.call_status = "Demo Call" if result.get("status") == "demo" else ("Called" if result["ok"] else "Blocked")
                self._log_delivery_result("Call", contact.name, result)
            time.sleep(0.75 if index < len(self.state.contacts) - 1 else 0)
        with self.lock:
            if run_id != self.state.run_id:
                return
            self.state.mode = "completed"
            self.state.system_status = "Accident Confirmed"
            self.state.alarm_state = "Dispatch Completed"
            self.state.dispatch_state = "Messages + Calls Sent"
            self.state.active_timer = "Completed"
            self.state.current_stage = "Full emergency escalation completed"
            self.state.recipients_summary = "All responders notified by SMS and call"
            self.state.banner = "Emergency escalation completed. Messages and calls were sent to saved responders."
            self._append_log("Automatic calling completed. Emergency responders have been escalated.", "danger")

    def _send_sms(self, contact: Contact) -> dict[str, Any]:
        if self.state.demo_mode:
            return {"ok": True, "status": "demo", "sid": "DEMO-SMS"}
        message = build_emergency_sms(self.state.vehicle_number, self.state.location_text, self.state.event_time)
        return self.twilio_service.send_sms(message, contact.number)

    def _make_call(self, contact: Contact) -> dict[str, Any]:
        if self.state.demo_mode:
            return {"ok": True, "status": "demo", "sid": "DEMO-CALL"}
        message = build_voice_message(self.state.vehicle_number, self.state.location_text, self.state.event_time)
        return self.twilio_service.make_call(message, contact.number)

    def _log_delivery_result(self, action: str, name: str, result: dict[str, Any]) -> None:
        if result.get("ok"):
            demo_note = " in demo mode" if result.get("status") == "demo" else ""
            self._append_log(f"{action} to {name} completed{demo_note}. SID: {result.get('sid', 'N/A')}", "success")
            return
        error = result.get("error_message", "Unknown delivery issue.")
        self._append_log(f"{action} to {name} blocked or failed: {error}", "warning")


CONTROLLER = AccidentDashboardController()


class DashboardRequestHandler(BaseHTTPRequestHandler):
    server_version = "AccidentDashboard/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        if path == "/":
            self._send_file(TEMPLATES_DIR / "index.html", "text/html; charset=utf-8")
            return
        if path == "/service-bay":
            self._send_file(TEMPLATES_DIR / "service_bay.html", "text/html; charset=utf-8")
            return
        if path == "/garage-setup":
            self._send_file(TEMPLATES_DIR / "garage_setup.html", "text/html; charset=utf-8")
            return
        if path == "/api/state":
            self._send_json(CONTROLLER.get_state())
            return
        if path in {"/favicon.ico", "/favicon.png", "/apple-touch-icon.png"}:
            target = (STATIC_DIR / path.lstrip("/")).resolve()
            if target.exists():
                self._send_file(target)
                return
        if path.startswith("/static/"):
            relative = path.removeprefix("/static/")
            target = (STATIC_DIR / relative).resolve()
            if STATIC_DIR.resolve() in target.parents:
                self._send_file(target)
                return
        self._send_json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        payload = self._read_json()
        if parsed.path == "/api/action":
            action = str(payload.get("action", ""))
            self._handle_action(action)
            return
        if parsed.path == "/api/settings":
            self._send_json(CONTROLLER.update_settings(payload))
            return
        if parsed.path == "/api/contact":
            self._send_json(CONTROLLER.update_contact(payload))
            return
        self._send_json({"error": "Not found"}, status=404)

    def _handle_action(self, action: str) -> None:
        actions = {
            "simulate_accident": CONTROLLER.simulate_accident,
            "driver_responded": CONTROLLER.driver_responded,
            "cancel_false_alarm": CONTROLLER.cancel_false_alarm,
            "call_contacts_now": CONTROLLER.call_contacts_now,
            "send_sms_now": CONTROLLER.send_sms_now,
            "reset": CONTROLLER.reset,
        }
        handler = actions.get(action)
        if not handler:
            self._send_json({"ok": False, "error": "Unknown action."}, status=400)
            return
        handler()
        self._send_json({"ok": True})

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_file(self, path: Path, content_type: str | None = None) -> None:
        if not path.exists() or not path.is_file():
            self._send_json({"error": "File not found"}, status=404)
            return
        data = path.read_bytes()
        guessed_type = content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", guessed_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: Any) -> None:
        return


def run(host: str = "127.0.0.1", port: int = 8080, open_browser: bool = True) -> None:
    server = ThreadingHTTPServer((host, port), DashboardRequestHandler)
    url = f"http://{host}:{port}"
    print(f"Smart Accident Dashboard running at {url}")
    print("Press Ctrl+C to stop.")
    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the smart accident web dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8080, type=int)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    run(host=args.host, port=args.port, open_browser=not args.no_browser)
