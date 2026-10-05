import tkinter as tk
import threading
from datetime import datetime
from pathlib import Path

from twilio import TwilioService, build_emergency_sms, build_voice_message


class SmartAccidentDashboard:
    """Demo dashboard for a smart accident detection and alert escalation system."""

    BG = "#0b1220"
    CARD = "#111827"
    PRIMARY = "#38bdf8"
    PRIMARY_LIGHT = "#172554"
    SUCCESS = "#34d399"
    SUCCESS_BG = "#083d2e"
    WARNING = "#f59e0b"
    WARNING_BG = "#4a2e05"
    DANGER = "#f87171"
    DANGER_BG = "#4c1217"
    PANEL = "#020617"
    TEXT = "#e5eefc"
    MUTED = "#94a3b8"
    BORDER = "#243244"
    BUTTON_TEXT = "#f8fafc"
    BUTTON_DISABLED_TEXT = "#cbd5e1"

    DRIVER_RESPONSE_SECONDS = 30
    CONTACT_ACK_SECONDS = 15
    MAX_EMERGENCY_CONTACTS = 10

    def __init__(self, root):
        self.root = root
        self.root.title("Smart Accident Detection & Driver Monitoring System")
        self.root.geometry("1360x790")
        self.root.minsize(1180, 720)
        self.root.configure(bg=self.BG)

        ico_file = Path(__file__).resolve().parent / "static" / "favicon.ico"
        if ico_file.exists():
            try:
                self.root.iconbitmap(str(ico_file))
            except Exception:
                pass

        self.vehicle_number = "TN 01 AB 1234"
        self.location_text = "11.0168, 76.9558  |  Coimbatore Bypass"
        self.emergency_contacts = self._build_emergency_contacts()
        self.service_contacts = [
            {"name": "Ambulance Service", "number": "+91XXXXXXXX11"},
            {"name": "Police Control Room", "number": "+91XXXXXXXX12"},
            {"name": "Nearest Hospital", "number": "+91XXXXXXXX13"},
        ]
        self.recipients = self.emergency_contacts + self.service_contacts
        self.twilio_service = TwilioService()

        self.current_mode = "normal"
        self.pending_jobs = []
        self.driver_timer_seconds = self.DRIVER_RESPONSE_SECONDS
        self.contact_timer_seconds = self.CONTACT_ACK_SECONDS
        self.workflow_run_id = 0

        self._build_ui()
        self.reset_system(initial=True)

    def _build_emergency_contacts(self):
        seeded_numbers = [
            "+919715252055",
            "+919994138347",
            "+916381681459",
            "+918903971809",
            "+917708009353",
        ]
        contacts = []
        for index in range(self.MAX_EMERGENCY_CONTACTS):
            if index < len(seeded_numbers):
                number = seeded_numbers[index]
            else:
                number = f"+91XXXXXXXX{index + 1:02d}"
            contacts.append(
                {
                    "name": f"Emergency Contact {index + 1}",
                    "number": number,
                }
            )
        return contacts

    def _build_ui(self):
        header = tk.Frame(self.root, bg=self.BG)
        header.pack(fill="x", padx=24, pady=(22, 12))

        tk.Label(
            header,
            text="Smart Accident Detection & Driver Monitoring System",
            font=("Segoe UI Semibold", 24),
            fg=self.TEXT,
            bg=self.BG,
        ).pack(anchor="w")

        tk.Label(
            header,
            text=(
                "Demo dashboard showing accident detection, alarm activation, 30-second driver response handling, "
                "automatic message alerts, and final automatic call escalation."
            ),
            font=("Segoe UI", 10),
            fg=self.MUTED,
            bg=self.BG,
        ).pack(anchor="w", pady=(5, 0))

        summary_row = tk.Frame(self.root, bg=self.BG)
        summary_row.pack(fill="x", padx=24, pady=(0, 14))

        self.status_badge = self._create_summary_card(summary_row, "System Status", "Monitoring Normal", self.SUCCESS, self.SUCCESS_BG)
        self.alarm_badge = self._create_summary_card(summary_row, "Alarm State", "Silent", self.PRIMARY, self.PRIMARY_LIGHT)
        self.notification_badge = self._create_summary_card(summary_row, "Alert Dispatch", "Standby", self.PRIMARY, self.PRIMARY_LIGHT)
        self.timer_badge = self._create_summary_card(summary_row, "Active Timer", "--:--", self.PRIMARY, self.PRIMARY_LIGHT)

        banner_card = tk.Frame(self.root, bg=self.CARD, highlightbackground=self.BORDER, highlightthickness=1)
        banner_card.pack(fill="x", padx=24, pady=(0, 14))

        self.banner = tk.Label(
            banner_card,
            text="System is monitoring the vehicle continuously. No accident event is active.",
            font=("Segoe UI", 10),
            fg=self.SUCCESS,
            bg=self.SUCCESS_BG,
            anchor="w",
            padx=16,
            pady=12,
        )
        self.banner.pack(fill="x", padx=16, pady=16)

        content = tk.Frame(self.root, bg=self.BG)
        content.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        left_column = tk.Frame(content, bg=self.BG)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right_column = tk.Frame(content, bg=self.BG)
        right_column.pack(side="left", fill="both", expand=True, padx=(10, 0))

        self._build_details_panel(left_column)
        self._build_logic_panel(left_column)
        self._build_controls_panel(right_column)
        self._build_log_panel(right_column)

    def _build_details_panel(self, parent):
        details_card = tk.Frame(parent, bg=self.CARD, highlightbackground=self.BORDER, highlightthickness=1)
        details_card.pack(fill="x", pady=(0, 14))

        tk.Label(
            details_card,
            text="Accident Event Details",
            font=("Segoe UI Semibold", 15),
            fg=self.TEXT,
            bg=self.CARD,
        ).pack(anchor="w", padx=18, pady=(18, 6))

        tk.Label(
            details_card,
            text="Important values stay visible throughout the simulation so the logic is easy to explain during the demo.",
            font=("Segoe UI", 10),
            fg=self.MUTED,
            bg=self.CARD,
        ).pack(anchor="w", padx=18, pady=(0, 14))

        grid = tk.Frame(details_card, bg=self.CARD)
        grid.pack(fill="x", padx=18, pady=(0, 18))
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)
        grid.grid_columnconfigure(2, weight=1)

        self.vehicle_value = self._create_detail_card(grid, 0, 0, "Vehicle Number", self.vehicle_number)
        self.location_value = self._create_detail_card(grid, 0, 1, "Location", self.location_text)
        self.time_value = self._create_detail_card(grid, 0, 2, "Last Event Time", "--:--")
        self.stage_value = self._create_detail_card(grid, 1, 0, "Current Stage", "Continuous monitoring active", self.MUTED)
        self.driver_response_value = self._create_detail_card(grid, 1, 1, "Driver Response", "Waiting for normal operation", self.MUTED)
        self.recipients_value = self._create_detail_card(grid, 1, 2, "Recipients", "No alerts sent yet", self.MUTED)

    def _build_logic_panel(self, parent):
        flow_card = tk.Frame(parent, bg=self.CARD, highlightbackground=self.BORDER, highlightthickness=1)
        flow_card.pack(fill="both", expand=True)

        tk.Label(
            flow_card,
            text="System Logic Flow",
            font=("Segoe UI Semibold", 15),
            fg=self.TEXT,
            bg=self.CARD,
        ).pack(anchor="w", padx=18, pady=(18, 6))

        tk.Label(
            flow_card,
            text="This section explains the exact logic implemented in the UI.",
            font=("Segoe UI", 10),
            fg=self.MUTED,
            bg=self.CARD,
        ).pack(anchor="w", padx=18, pady=(0, 14))

        steps = [
            "1. Accident sensor detects a collision and immediately triggers the alarm, buzzer, and emergency warning state.",
            "2. A 30-second timer starts and the system waits for the driver to respond or cancel the alert.",
            "3. If the driver does not respond within 30 seconds, emergency SMS alerts are sent automatically.",
            "4. Alerts are sent to saved emergency contacts, ambulance, police, and the nearest hospital.",
            "5. If the message is not acknowledged, the system automatically starts calling the same responders.",
            "6. The demo also supports false alarm cancellation and acknowledgement during the presentation.",
        ]

        for step in steps:
            row = tk.Frame(flow_card, bg=self.PRIMARY_LIGHT, padx=14, pady=12)
            row.pack(fill="x", padx=18, pady=6)
            tk.Label(
                row,
                text=step,
                font=("Segoe UI", 10),
                fg=self.TEXT,
                bg=self.PRIMARY_LIGHT,
                wraplength=620,
                justify="left",
            ).pack(anchor="w")

    def _build_controls_panel(self, parent):
        controls_card = tk.Frame(parent, bg=self.CARD, highlightbackground=self.BORDER, highlightthickness=1)
        controls_card.pack(fill="x", pady=(0, 14))

        tk.Label(
            controls_card,
            text="Simulation Controls",
            font=("Segoe UI Semibold", 15),
            fg=self.TEXT,
            bg=self.CARD,
        ).pack(anchor="w", padx=18, pady=(18, 6))

        tk.Label(
            controls_card,
            text="Use these buttons to demonstrate both successful response and automatic escalation cases.",
            font=("Segoe UI", 10),
            fg=self.MUTED,
            bg=self.CARD,
        ).pack(anchor="w", padx=18, pady=(0, 14))

        grid = tk.Frame(controls_card, bg=self.CARD)
        grid.pack(fill="x", padx=18, pady=(0, 18))
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        self.accident_button = self._create_action_button(
            grid,
            "Simulate Accident Detection",
            self.simulate_accident_detection,
            "#7f1d1d",
            "#991b1b",
            "#4b1d1f",
            0,
            0,
        )
        self.driver_response_button = self._create_action_button(
            grid,
            "Driver Responded",
            self.driver_responded,
            "#14532d",
            "#166534",
            "#243f32",
            0,
            1,
        )
        self.contact_ack_button = self._create_action_button(
            grid,
            "Call Contacts Now",
            self.call_contacts_now,
            "#78350f",
            "#92400e",
            "#4a301b",
            1,
            0,
        )
        self.cancel_button = self._create_action_button(
            grid,
            "Cancel False Alarm",
            self.cancel_false_alarm,
            "#1d4ed8",
            "#1e40af",
            "#25344f",
            1,
            1,
        )
        self.reset_button = self._create_action_button(
            grid,
            "Reset System",
            self.reset_system,
            "#0f766e",
            "#115e59",
            "#214543",
            2,
            0,
            columnspan=2,
        )

    def _build_log_panel(self, parent):
        log_card = tk.Frame(parent, bg=self.CARD, highlightbackground=self.BORDER, highlightthickness=1)
        log_card.pack(fill="both", expand=True)

        tk.Label(
            log_card,
            text="Live Emergency Workflow Log",
            font=("Segoe UI Semibold", 15),
            fg=self.TEXT,
            bg=self.CARD,
        ).pack(anchor="w", padx=18, pady=(18, 6))

        tk.Label(
            log_card,
            text="Every important action is time-stamped to make the system behavior clear in the project presentation.",
            font=("Segoe UI", 10),
            fg=self.MUTED,
            bg=self.CARD,
        ).pack(anchor="w", padx=18, pady=(0, 12))

        self.log_box = tk.Text(
            log_card,
            height=24,
            bg=self.PANEL,
            fg="#f8fafc",
            insertbackground="#f8fafc",
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            padx=14,
            pady=14,
        )
        self.log_box.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        self.log_box.tag_config("time", foreground="#98a2b3")
        self.log_box.tag_config("normal", foreground="#bbf7d0")
        self.log_box.tag_config("warning", foreground="#fde68a")
        self.log_box.tag_config("alert", foreground="#fecaca")
        self.log_box.tag_config("info", foreground="#bfdbfe")
        self.log_box.config(state="disabled")

    def _create_summary_card(self, parent, title, value, fg, bg):
        card = tk.Frame(parent, bg=self.CARD, highlightbackground=self.BORDER, highlightthickness=1)
        card.pack(side="left", fill="both", expand=True, padx=6)

        tk.Label(
            card,
            text=title,
            font=("Segoe UI Semibold", 10),
            fg=self.MUTED,
            bg=self.CARD,
        ).pack(anchor="w", padx=18, pady=(16, 8))

        badge = tk.Label(
            card,
            text=value,
            font=("Segoe UI Semibold", 16),
            fg=fg,
            bg=bg,
            padx=14,
            pady=8,
        )
        badge.pack(anchor="w", padx=18, pady=(0, 16))
        return badge

    def _create_detail_card(self, parent, row, column, title, value, color=None):
        card = tk.Frame(parent, bg=self.PRIMARY_LIGHT, padx=14, pady=14)
        card.grid(row=row, column=column, sticky="nsew", padx=6, pady=6)
        parent.grid_rowconfigure(row, weight=1)

        tk.Label(
            card,
            text=title,
            font=("Segoe UI Semibold", 10),
            fg=self.MUTED,
            bg=self.PRIMARY_LIGHT,
        ).pack(anchor="w")

        label = tk.Label(
            card,
            text=value,
            font=("Segoe UI", 12),
            fg=color or self.TEXT,
            bg=self.PRIMARY_LIGHT,
            wraplength=260,
            justify="left",
        )
        label.pack(anchor="w", pady=(8, 0))
        return label

    def _create_action_button(self, parent, text, command, bg, active_bg, disabled_bg, row, column, columnspan=1):
        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=self.BUTTON_TEXT,
            activebackground=active_bg,
            activeforeground=self.BUTTON_TEXT,
            disabledforeground=self.BUTTON_DISABLED_TEXT,
            relief="flat",
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            font=("Segoe UI Semibold", 11),
            padx=16,
            pady=12,
            wraplength=240,
        )
        button.enabled_bg = bg
        button.active_bg = active_bg
        button.disabled_bg = disabled_bg
        button.grid(row=row, column=column, columnspan=columnspan, sticky="ew", padx=6, pady=6)
        return button

    def _apply_button_state(self, button, enabled):
        if enabled:
            button.config(
                state="normal",
                bg=button.enabled_bg,
                fg=self.BUTTON_TEXT,
                activebackground=button.active_bg,
                activeforeground=self.BUTTON_TEXT,
                cursor="hand2",
            )
            return

        button.config(
            state="disabled",
            bg=button.disabled_bg,
            fg=self.BUTTON_DISABLED_TEXT,
            disabledforeground=self.BUTTON_DISABLED_TEXT,
            cursor="arrow",
        )

    def _set_badge(self, widget, text, fg, bg):
        widget.config(text=text, fg=fg, bg=bg)

    def _set_detail(self, widget, text, color=None):
        widget.config(text=text, fg=color or self.TEXT)

    def _set_banner(self, text, fg, bg):
        self.banner.config(text=text, fg=fg, bg=bg)

    def _append_log(self, message, tag="info"):
        timestamp = datetime.now().strftime("%I:%M:%S %p")
        self.log_box.config(state="normal")
        self.log_box.insert(tk.END, f"[{timestamp}] ", "time")
        self.log_box.insert(tk.END, f"{message}\n", tag)
        self.log_box.see(tk.END)
        self.log_box.config(state="disabled")

    def _recipient_label(self, prefix="Recipients"):
        return (
            f"{prefix}: {len(self.emergency_contacts)} emergency contacts + "
            "ambulance, police, hospital"
        )

    def _event_time_text(self):
        value = self.time_value.cget("text")
        return value if value != "--:--" else datetime.now().strftime("%d-%m-%Y  %I:%M:%S %p")

    def _send_sms_to_recipient(self, recipient, run_id):
        message = build_emergency_sms(
            self.vehicle_number,
            self.location_text,
            self._event_time_text(),
        )
        self._run_twilio_request_async(
            "SMS",
            recipient["name"],
            run_id,
            lambda: self.twilio_service.send_sms(message, recipient["number"]),
        )

    def _call_recipient(self, recipient, run_id):
        message = build_voice_message(
            self.vehicle_number,
            self.location_text,
            self._event_time_text(),
        )
        self._run_twilio_request_async(
            "Call",
            recipient["name"],
            run_id,
            lambda: self.twilio_service.make_call(message, recipient["number"]),
        )

    def _run_twilio_request_async(self, action, recipient_name, run_id, request_callback):
        def worker():
            result = request_callback()
            self.root.after(
                0,
                lambda: self._handle_twilio_result(action, recipient_name, result, run_id),
            )

        threading.Thread(target=worker, daemon=True).start()

    def _handle_twilio_result(self, action, recipient_name, result, run_id):
        if run_id != self.workflow_run_id:
            return
        self._log_twilio_result(action, recipient_name, result)

    def _log_twilio_result(self, action, recipient_name, result):
        if result["ok"]:
            self._append_log(
                f"{action} sent to {recipient_name} successfully. SID: {result.get('sid', 'N/A')}",
                "normal",
            )
            return

        if result["status"] in {"skipped", "invalid_configuration"}:
            self._append_log(
                f"{action} to {recipient_name} is blocked by configuration: {result.get('error_message', 'Unknown configuration issue.')}",
                "warning",
            )
            if result.get("more_info"):
                self._append_log(result["more_info"], "info")
            return

        self._append_log(
            f"{action} to {recipient_name} failed: {result.get('error_message', 'Unknown Twilio error.')}",
            "alert",
        )
        if result.get("error_code"):
            self._append_log(f"Twilio error code: {result['error_code']}", "alert")

    def _format_seconds(self, seconds):
        minutes, secs = divmod(seconds, 60)
        return f"{minutes:02d}:{secs:02d}"

    def _stamp_event_time(self):
        self._set_detail(self.time_value, datetime.now().strftime("%d-%m-%Y  %I:%M:%S %p"))

    def _bump_workflow_run(self):
        self.workflow_run_id += 1
        return self.workflow_run_id

    def _remove_pending_job(self, job_id):
        if job_id in self.pending_jobs:
            self.pending_jobs.remove(job_id)

    def _clear_pending_jobs(self):
        for job in list(self.pending_jobs):
            try:
                self.root.after_cancel(job)
            except tk.TclError:
                pass
        self.pending_jobs.clear()

    def _schedule_job(self, delay_ms, callback):
        job_id = None

        def step():
            self._remove_pending_job(job_id)
            callback()

        job_id = self.root.after(delay_ms, step)
        self.pending_jobs.append(job_id)
        return job_id

    def _schedule_step(self, delay_ms, message, tag="info", callback=None):
        def step():
            self._append_log(message, tag)
            if callback:
                callback()

        self._schedule_job(delay_ms, step)

    def _set_button_states(self, mode):
        if mode == "normal":
            self._apply_button_state(self.accident_button, True)
            self._apply_button_state(self.driver_response_button, False)
            self._apply_button_state(self.contact_ack_button, True)
            self._apply_button_state(self.cancel_button, False)
            self._apply_button_state(self.reset_button, True)
            return

        if mode == "driver_wait":
            self._apply_button_state(self.accident_button, False)
            self._apply_button_state(self.driver_response_button, True)
            self._apply_button_state(self.contact_ack_button, True)
            self._apply_button_state(self.cancel_button, True)
            self._apply_button_state(self.reset_button, True)
            return

        if mode == "message_dispatch":
            self._apply_button_state(self.accident_button, False)
            self._apply_button_state(self.driver_response_button, False)
            self._apply_button_state(self.contact_ack_button, True)
            self._apply_button_state(self.cancel_button, True)
            self._apply_button_state(self.reset_button, True)
            return

        if mode == "contact_wait":
            self._apply_button_state(self.accident_button, False)
            self._apply_button_state(self.driver_response_button, False)
            self._apply_button_state(self.contact_ack_button, True)
            self._apply_button_state(self.cancel_button, True)
            self._apply_button_state(self.reset_button, True)
            return

        self._apply_button_state(self.accident_button, True)
        self._apply_button_state(self.driver_response_button, False)
        self._apply_button_state(self.contact_ack_button, True)
        self._apply_button_state(self.cancel_button, False)
        self._apply_button_state(self.reset_button, True)

    def simulate_accident_detection(self):
        self._bump_workflow_run()
        self._clear_pending_jobs()
        self.current_mode = "driver_wait"
        self.driver_timer_seconds = self.DRIVER_RESPONSE_SECONDS
        self._stamp_event_time()
        self._set_button_states("driver_wait")

        self._set_badge(self.status_badge, "Accident Detected", self.DANGER, self.DANGER_BG)
        self._set_badge(self.alarm_badge, "Alarm Triggered", self.DANGER, self.DANGER_BG)
        self._set_badge(self.notification_badge, "Waiting For Driver", self.WARNING, self.WARNING_BG)
        self._set_badge(self.timer_badge, self._format_seconds(self.driver_timer_seconds), self.WARNING, self.WARNING_BG)

        self._set_detail(self.stage_value, "Accident detected, buzzer alarm started", self.DANGER)
        self._set_detail(self.driver_response_value, "Driver must respond within 30 seconds", self.WARNING)
        self._set_detail(self.recipients_value, self._recipient_label(), self.TEXT)
        self._set_banner(
            "Accident detected. Alarm is active and the system is waiting 30 seconds for driver response before sending alerts.",
            self.DANGER,
            self.DANGER_BG,
        )

        self._append_log("Accident sensor detected a collision. Emergency mode activated.", "alert")
        self._append_log("Alarm, buzzer, and dashboard warning indicators turned ON immediately.", "warning")
        self._append_log("Driver response countdown started for 30 seconds.", "info")
        self._run_driver_countdown()

    def _run_driver_countdown(self):
        if self.current_mode != "driver_wait":
            return

        self._set_badge(self.timer_badge, self._format_seconds(self.driver_timer_seconds), self.WARNING, self.WARNING_BG)

        if self.driver_timer_seconds in {20, 10, 5}:
            self._append_log(
                f"{self.driver_timer_seconds} seconds remaining for driver acknowledgement.",
                "warning",
            )

        if self.driver_timer_seconds == 0:
            self._append_log("No driver response received within 30 seconds.", "alert")
            self._begin_message_dispatch()
            return

        self.driver_timer_seconds -= 1
        self._schedule_job(1000, self._run_driver_countdown)

    def driver_responded(self):
        if self.current_mode != "driver_wait":
            self._append_log("Driver response button pressed, but there is no active driver response timer.", "info")
            return

        self._clear_pending_jobs()
        self.current_mode = "resolved"
        self._stamp_event_time()
        self._set_button_states("resolved")

        self._set_badge(self.status_badge, "Driver Responded", self.SUCCESS, self.SUCCESS_BG)
        self._set_badge(self.alarm_badge, "Alarm Stopped", self.SUCCESS, self.SUCCESS_BG)
        self._set_badge(self.notification_badge, "No Alerts Sent", self.PRIMARY, self.PRIMARY_LIGHT)
        self._set_badge(self.timer_badge, "Resolved", self.SUCCESS, self.SUCCESS_BG)

        self._set_detail(self.stage_value, "Emergency stopped after driver response", self.SUCCESS)
        self._set_detail(self.driver_response_value, "Driver confirmed safe / conscious", self.SUCCESS)
        self._set_detail(self.recipients_value, "Emergency messages cancelled", self.SUCCESS)
        self._set_banner(
            "Driver responded within the allowed time. Alarm stopped and emergency notification was cancelled.",
            self.SUCCESS,
            self.SUCCESS_BG,
        )

        self._append_log("Driver responded within the response window.", "normal")
        self._append_log("Alarm cleared and no emergency message was sent.", "normal")

    def _begin_message_dispatch(self):
        self.current_mode = "message_dispatch"
        self._set_button_states("message_dispatch")
        run_id = self.workflow_run_id

        self._set_badge(self.notification_badge, "Sending SMS Alerts", self.DANGER, self.DANGER_BG)
        self._set_badge(self.alarm_badge, "Alarm Active", self.DANGER, self.DANGER_BG)
        self._set_detail(self.stage_value, "Sending emergency SMS alerts automatically", self.DANGER)
        self._set_detail(self.driver_response_value, "Driver did not respond", self.DANGER)
        self._set_banner(
            "Driver did not respond. The system is now sending emergency messages automatically.",
            self.DANGER,
            self.DANGER_BG,
        )

        delay = 0
        for recipient in self.recipients:
            self._schedule_step(
                delay,
                f"Dispatching SMS alert to {recipient['name']}.",
                "alert",
                callback=lambda data=recipient, active_run=run_id: self._send_sms_to_recipient(data, active_run),
            )
            delay += 900

        self._schedule_step(
            delay,
            "All emergency messages delivered. Waiting for acknowledgement before automatic calling begins.",
            "alert",
            callback=self._start_contact_ack_timer,
        )

    def _start_contact_ack_timer(self):
        self.current_mode = "contact_wait"
        self.contact_timer_seconds = self.CONTACT_ACK_SECONDS
        self._set_button_states("contact_wait")

        self._set_badge(self.notification_badge, "Waiting For Acknowledgement", self.WARNING, self.WARNING_BG)
        self._set_badge(self.timer_badge, self._format_seconds(self.contact_timer_seconds), self.WARNING, self.WARNING_BG)
        self._set_detail(self.stage_value, "Messages sent, waiting for acknowledgement", self.WARNING)
        self._set_detail(self.recipients_value, self._recipient_label(), self.TEXT)
        self._set_banner(
            "Emergency SMS alerts were sent. If nobody acknowledges the alert, automatic calling will start.",
            self.WARNING,
            self.WARNING_BG,
        )

        self._append_log(
            "Acknowledgement timer started for message response before automatic call escalation.",
            "info",
        )
        self._run_contact_countdown()

    def _run_contact_countdown(self):
        if self.current_mode != "contact_wait":
            return

        self._set_badge(self.timer_badge, self._format_seconds(self.contact_timer_seconds), self.WARNING, self.WARNING_BG)

        if self.contact_timer_seconds in {10, 5}:
            self._append_log(
                f"{self.contact_timer_seconds} seconds remaining for contact acknowledgement.",
                "warning",
            )

        if self.contact_timer_seconds == 0:
            self._append_log("No acknowledgement received for the emergency message alerts.", "alert")
            self._begin_auto_calls()
            return

        self.contact_timer_seconds -= 1
        self._schedule_job(1000, self._run_contact_countdown)

    def call_contacts_now(self):
        if self.current_mode == "auto_calling":
            self._append_log("Automatic contact calling is already in progress.", "info")
            return

        self._bump_workflow_run()
        self._clear_pending_jobs()
        self._stamp_event_time()
        if self.current_mode == "normal":
            self._set_badge(self.status_badge, "Manual Emergency Call", self.DANGER, self.DANGER_BG)
            self._append_log("Manual emergency call button pressed from standby mode.", "warning")
        else:
            self._append_log("Manual contact call button pressed. Escalating directly to phone calls.", "warning")

        self._begin_auto_calls(manual_trigger=True)

    def _begin_auto_calls(self, manual_trigger=False):
        self.current_mode = "auto_calling"
        self._set_button_states("resolved")
        run_id = self.workflow_run_id

        self._set_badge(self.alarm_badge, "Call Escalation Active", self.DANGER, self.DANGER_BG)
        self._set_badge(self.notification_badge, "Automatic Calling", self.DANGER, self.DANGER_BG)
        self._set_badge(self.timer_badge, "Calling", self.DANGER, self.DANGER_BG)
        if manual_trigger:
            self._set_badge(self.status_badge, "Calling Contacts", self.DANGER, self.DANGER_BG)

        self._set_detail(self.stage_value, "Calling emergency responders automatically", self.DANGER)
        if manual_trigger:
            self._set_detail(self.driver_response_value, "Manual direct call requested by user", self.WARNING)
        else:
            self._set_detail(self.driver_response_value, "No response from driver", self.DANGER)
        self._set_detail(self.recipients_value, self._recipient_label(prefix="Calling"), self.DANGER)
        banner_text = "Direct contact calling is active. The system is now calling responders immediately."
        if not manual_trigger:
            banner_text = "No acknowledgement received. The system is now calling responders automatically."
        self._set_banner(banner_text, self.DANGER, self.DANGER_BG)

        delay = 0
        for recipient in self.recipients:
            self._schedule_step(
                delay,
                f"Starting automatic call to {recipient['name']}.",
                "alert",
                callback=lambda data=recipient, active_run=run_id: self._call_recipient(data, active_run),
            )
            delay += 1000

        self._schedule_step(
            delay,
            "Automatic calling completed. Emergency responders have been escalated successfully.",
            "alert",
            callback=self._complete_emergency_flow,
        )

    def _complete_emergency_flow(self):
        self.current_mode = "completed"
        self._set_button_states("resolved")
        self._stamp_event_time()

        self._set_badge(self.status_badge, "Accident Confirmed", self.DANGER, self.DANGER_BG)
        self._set_badge(self.alarm_badge, "Dispatch Completed", self.DANGER, self.DANGER_BG)
        self._set_badge(self.notification_badge, "Messages + Calls Sent", self.DANGER, self.DANGER_BG)
        self._set_badge(self.timer_badge, "Completed", self.DANGER, self.DANGER_BG)

        self._set_detail(self.stage_value, "Full emergency escalation completed", self.DANGER)
        self._set_detail(self.driver_response_value, "No response from driver", self.DANGER)
        self._set_detail(self.recipients_value, "All responders notified by SMS and call", self.DANGER)
        self._set_banner(
            "Emergency escalation completed. Messages and calls were sent to saved contacts, ambulance, police, and hospital.",
            self.DANGER,
            self.DANGER_BG,
        )

    def cancel_false_alarm(self):
        if self.current_mode == "normal":
            self._append_log("False alarm cancellation requested, but no emergency workflow is active.", "info")
            return

        self._bump_workflow_run()
        self._clear_pending_jobs()
        self.current_mode = "resolved"
        self._stamp_event_time()
        self._set_button_states("resolved")

        self._set_badge(self.status_badge, "False Alarm Cancelled", self.SUCCESS, self.SUCCESS_BG)
        self._set_badge(self.alarm_badge, "Alarm Stopped", self.SUCCESS, self.SUCCESS_BG)
        self._set_badge(self.notification_badge, "Escalation Cancelled", self.PRIMARY, self.PRIMARY_LIGHT)
        self._set_badge(self.timer_badge, "Cancelled", self.SUCCESS, self.SUCCESS_BG)

        self._set_detail(self.stage_value, "Emergency workflow stopped manually", self.SUCCESS)
        self._set_detail(self.driver_response_value, "False alarm marked by user", self.SUCCESS)
        self._set_detail(self.recipients_value, "No further alerts will be sent", self.SUCCESS)
        self._set_banner(
            "False alarm cancelled. The system stopped the emergency workflow and returned to safe standby mode.",
            self.SUCCESS,
            self.SUCCESS_BG,
        )

        self._append_log("User cancelled the alert as a false alarm.", "normal")
        self._append_log("Pending messages, calls, and escalation timers were stopped.", "normal")

    def reset_system(self, initial=False):
        self._bump_workflow_run()
        self._clear_pending_jobs()
        self.current_mode = "normal"
        self.driver_timer_seconds = self.DRIVER_RESPONSE_SECONDS
        self.contact_timer_seconds = self.CONTACT_ACK_SECONDS
        self._set_button_states("normal")

        self._set_badge(self.status_badge, "Monitoring Normal", self.SUCCESS, self.SUCCESS_BG)
        self._set_badge(self.alarm_badge, "Silent", self.PRIMARY, self.PRIMARY_LIGHT)
        self._set_badge(self.notification_badge, "Standby", self.PRIMARY, self.PRIMARY_LIGHT)
        self._set_badge(self.timer_badge, "--:--", self.PRIMARY, self.PRIMARY_LIGHT)

        self._set_detail(self.vehicle_value, self.vehicle_number)
        self._set_detail(self.location_value, self.location_text)
        self._set_detail(self.time_value, "--:--")
        self._set_detail(self.stage_value, "Continuous monitoring active", self.MUTED)
        self._set_detail(self.driver_response_value, "Waiting for normal operation", self.MUTED)
        self._set_detail(self.recipients_value, "No alerts sent yet", self.MUTED)
        self._set_banner(
            "System is monitoring the vehicle continuously. No accident event is active.",
            self.SUCCESS,
            self.SUCCESS_BG,
        )

        if initial:
            self._append_log("Dashboard initialized. Sensors, alarm module, SMS service, and call escalation are ready.", "normal")
        else:
            self._append_log("System reset completed. Dashboard returned to normal monitoring mode.", "normal")


def main():
    root = tk.Tk()
    SmartAccidentDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
