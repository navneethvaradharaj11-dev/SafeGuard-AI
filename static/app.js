const qs = (selector) => document.querySelector(selector);

const els = {
  body: document.body,
  modeDot: qs("#modeDot"),
  sideMode: qs("#sideMode"),
  twilioBadge: qs("#twilioBadge"),
  demoBadge: qs("#demoBadge"),
  systemStatus: qs("#systemStatus"),
  alarmState: qs("#alarmState"),
  dispatchState: qs("#dispatchState"),
  activeTimer: qs("#activeTimer"),
  banner: qs("#banner"),
  eventTime: qs("#eventTime"),
  vehicleNumber: qs("#vehicleNumber"),
  locationText: qs("#locationText"),
  currentStage: qs("#currentStage"),
  driverResponse: qs("#driverResponse"),
  recipientsSummary: qs("#recipientsSummary"),
  contactsBody: qs("#contactsBody"),
  logList: qs("#logList"),
  settingsForm: qs("#settingsForm"),
  vehicleInput: qs("#vehicleInput"),
  locationInput: qs("#locationInput"),
  demoModeInput: qs("#demoModeInput"),
  contactDialog: qs("#contactDialog"),
  contactForm: qs("#contactForm"),
  contactIndex: qs("#contactIndex"),
  contactName: qs("#contactName"),
  contactNumber: qs("#contactNumber"),
  closeDialog: qs("#closeDialog"),
  railAlertMode: qs("#railAlertMode"),
  railLastEvent: qs("#railLastEvent"),
  dispatchHeadline: qs("#dispatchHeadline"),
  dispatchSubline: qs("#dispatchSubline"),
  // Automotive UI Enhancements
  driverStatusBadge: qs("#driverStatusBadge"),
  driverAlertnessVal: qs("#driverAlertnessVal"),
  driverAlertnessFill: qs("#driverAlertnessFill"),
  driverEyeStatus: qs("#driverEyeStatus"),
  vehicleSensorStatus: qs("#vehicleSensorStatus"),
  sensorFront: qs("#sensorFront"),
  sensorRear: qs("#sensorRear"),
  sensorLeft: qs("#sensorLeft"),
  sensorRight: qs("#sensorRight"),
  emergencyHeaderBadge: qs("#emergencyHeaderBadge"),
  cabinBuzzerStatus: qs("#cabinBuzzerStatus"),
  impactGForce: qs("#impactGForce"),
  commGateway: qs("#commGateway"),
  saveFeedback: qs("#saveFeedback")
};

let lastContactsKey = "";

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

async function postAction(action) {
  try {
    await api("/api/action", {
      method: "POST",
      body: JSON.stringify({ action })
    });
    await refresh();
  } catch (err) {
    console.error("Action error:", err);
  }
}

function setText(element, value) {
  if (!element) return;
  element.textContent = value || "";
}

function setInputValue(input, value) {
  if (input && document.activeElement !== input) {
    input.value = value || "";
  }
}

function bind(element, eventName, handler) {
  if (element) {
    element.addEventListener(eventName, handler);
  }
}

function modeLabel(mode) {
  const labels = {
    normal: "Monitoring Normal",
    driver_wait: "Awaiting Driver Response",
    message_dispatch: "Sending Emergency SMS",
    contact_wait: "Awaiting Contact Ack",
    auto_calling: "Escalating Voice Calls",
    completed: "Dispatch Cycle Completed",
    resolved: "Resolved Safe"
  };
  return labels[mode] || mode;
}

function applyTheme(mode) {
  // Update Driver Monitoring UI
  if (els.driverStatusBadge) {
    els.driverStatusBadge.className = "status-badge";
    if (mode === "normal") {
      els.driverStatusBadge.classList.add("normal");
      setText(els.driverStatusBadge, "Awake");
      setText(els.driverAlertnessVal, "96%");
      if (els.driverAlertnessFill) {
        els.driverAlertnessFill.style.width = "96%";
        els.driverAlertnessFill.style.backgroundColor = "var(--success)";
      }
      setText(els.driverEyeStatus, "Normal");
    } else if (mode === "driver_wait") {
      els.driverStatusBadge.classList.add("warning");
      setText(els.driverStatusBadge, "Checking Response");
      setText(els.driverAlertnessVal, "55%");
      if (els.driverAlertnessFill) {
        els.driverAlertnessFill.style.width = "55%";
        els.driverAlertnessFill.style.backgroundColor = "var(--warning)";
      }
      setText(els.driverEyeStatus, "Closed / Warning");
    } else if (["message_dispatch", "contact_wait", "auto_calling", "completed"].includes(mode)) {
      els.driverStatusBadge.classList.add("danger");
      setText(els.driverStatusBadge, "Unresponsive");
      setText(els.driverAlertnessVal, "Critical");
      if (els.driverAlertnessFill) {
        els.driverAlertnessFill.style.width = "10%";
        els.driverAlertnessFill.style.backgroundColor = "var(--danger)";
      }
      setText(els.driverEyeStatus, "No Response");
    } else if (mode === "resolved") {
      els.driverStatusBadge.classList.add("normal");
      setText(els.driverStatusBadge, "Confirmed Safe");
      setText(els.driverAlertnessVal, "100%");
      if (els.driverAlertnessFill) {
        els.driverAlertnessFill.style.width = "100%";
        els.driverAlertnessFill.style.backgroundColor = "var(--success)";
      }
      setText(els.driverEyeStatus, "Normal");
    }
  }

  // Update Vehicle Top-View Sensors
  const isAccident = ["driver_wait", "message_dispatch", "contact_wait", "auto_calling", "completed"].includes(mode);
  if (els.vehicleSensorStatus) {
    els.vehicleSensorStatus.className = "status-badge " + (isAccident ? "danger" : "normal");
    setText(els.vehicleSensorStatus, isAccident ? "Impact Detected" : "4 Sensors Armed");
  }

  if (els.sensorFront) {
    els.sensorFront.classList.toggle("impact-alert", isAccident);
  }
  if (els.sensorLeft) {
    els.sensorLeft.classList.toggle("impact-alert", isAccident);
  }

  // Update Emergency Card Status
  if (els.emergencyHeaderBadge) {
    els.emergencyHeaderBadge.className = "status-badge";
    if (mode === "normal") {
      els.emergencyHeaderBadge.classList.add("normal");
      setText(els.emergencyHeaderBadge, "Standby");
    } else if (mode === "driver_wait" || mode === "contact_wait") {
      els.emergencyHeaderBadge.classList.add("warning");
      setText(els.emergencyHeaderBadge, "Timer Active");
    } else if (mode === "message_dispatch" || mode === "auto_calling") {
      els.emergencyHeaderBadge.classList.add("danger");
      setText(els.emergencyHeaderBadge, "Escalating");
    } else if (mode === "completed") {
      els.emergencyHeaderBadge.classList.add("danger");
      setText(els.emergencyHeaderBadge, "Dispatched");
    } else {
      els.emergencyHeaderBadge.classList.add("normal");
      setText(els.emergencyHeaderBadge, "Resolved");
    }
  }

  // Update In-Cabin Buzzer
  if (els.cabinBuzzerStatus) {
    if (mode === "normal") {
      setText(els.cabinBuzzerStatus, "Off (Nominal)");
    } else if (mode === "driver_wait") {
      setText(els.cabinBuzzerStatus, "Active (85dB Pulse)");
    } else if (["message_dispatch", "contact_wait", "auto_calling", "completed"].includes(mode)) {
      setText(els.cabinBuzzerStatus, "Active (Continuous)");
    } else {
      setText(els.cabinBuzzerStatus, "Muted");
    }
  }

  // Update Impact G-Force
  if (els.impactGForce) {
    if (isAccident) {
      setText(els.impactGForce, "4.85 G (Impact Threshold Exceeded)");
      els.impactGForce.style.color = "var(--danger)";
    } else if (mode === "resolved") {
      setText(els.impactGForce, "1.00 G (Stabilized)");
      els.impactGForce.style.color = "var(--text-primary)";
    } else {
      setText(els.impactGForce, "1.02 G (Nominal Vector)");
      els.impactGForce.style.color = "var(--text-primary)";
    }
  }
}

function updateTimeline(mode) {
  const order = ["normal", "driver_wait", "message_dispatch", "contact_wait", "auto_calling", "completed"];
  const activeIndex = Math.max(0, order.indexOf(mode === "resolved" ? "normal" : mode));
  document.querySelectorAll("#timeline [data-step]").forEach((step) => {
    const stepIndex = order.indexOf(step.dataset.step);
    step.classList.toggle("completed", stepIndex < activeIndex);
    step.classList.toggle("active", stepIndex === activeIndex);
    step.classList.toggle("pending", stepIndex > activeIndex);
  });
}

function updateDispatchPanel(state) {
  const copy = {
    normal: ["Monitoring clear", "Emergency alerts are on standby."],
    driver_wait: ["Driver response timer active", "Waiting before emergency alert dispatch."],
    message_dispatch: ["Emergency alerts sent", "Calling emergency services is queued if nobody acknowledges."],
    contact_wait: ["SMS sent, awaiting acknowledgement", "Automatic calls will start if no response is received."],
    auto_calling: ["Calling emergency services", "Voice escalation is active for saved responders."],
    completed: ["Escalation cycle completed", "Messages and calls were dispatched."],
    resolved: ["Emergency flow resolved", "No active dispatch is running."]
  };
  const [headline, subline] = copy[state.mode] || copy.normal;
  setText(els.dispatchHeadline, headline);
  setText(els.dispatchSubline, subline);
}

function formatRole(role) {
  const clean = String(role || "Responder");
  if (clean.toLowerCase().includes("family")) {
    return `<span class="role-badge family">Family / Personal</span>`;
  }
  return `<span class="role-badge responder">${escapeHtml(clean)}</span>`;
}

function chip(status) {
  const val = String(status || "Standby");
  const normalized = val.toLowerCase().replace(/\s+/g, "-");
  return `<span class="status-chip ${normalized}">${escapeHtml(val)}</span>`;
}

function renderContacts(contacts) {
  if (!els.contactsBody) return;
  const key = JSON.stringify(contacts);
  if (key === lastContactsKey) return;
  lastContactsKey = key;
  els.contactsBody.innerHTML = contacts.map((contact, index) => `
    <tr>
      <td style="font-weight: 600;">${escapeHtml(contact.name)}</td>
      <td>${formatRole(contact.role)}</td>
      <td style="font-family: ui-monospace, monospace; color: var(--text-secondary);">${escapeHtml(contact.number)}</td>
      <td>${chip(contact.sms_status)}</td>
      <td>${chip(contact.call_status)}</td>
      <td style="text-align: right;"><button type="button" data-edit="${index}">Edit</button></td>
    </tr>
  `).join("");
}

function renderLogs(logs) {
  if (!els.logList) return;
  els.logList.innerHTML = logs.slice(-80).map((entry) => `
    <div class="log-row ${escapeHtml(entry.level)}">
      <time>${escapeHtml(entry.time)}</time>
      <span>${escapeHtml(entry.message)}</span>
    </div>
  `).join("");
  els.logList.scrollTop = els.logList.scrollHeight;
}

function escapeHtml(value) {
  return String(value || "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  })[character]);
}

function renderState(state) {
  setText(els.sideMode, modeLabel(state.mode));
  setText(els.systemStatus, state.system_status);
  setText(els.alarmState, state.alarm_state);
  setText(els.dispatchState, state.dispatch_state);
  setText(els.activeTimer, state.active_timer);
  setText(els.banner, state.banner);
  setText(els.eventTime, state.event_time);
  setText(els.vehicleNumber, state.vehicle_number);
  setText(els.locationText, state.location_text);
  setText(els.currentStage, state.current_stage);
  setText(els.driverResponse, state.driver_response);
  setText(els.recipientsSummary, state.recipients_summary);

  // Honest Integration and Mode Badges
  if (els.twilioBadge) {
    if (state.twilio_ready) {
      els.twilioBadge.className = "lamp ready";
      els.twilioBadge.textContent = "Twilio: Ready";
    } else {
      els.twilioBadge.className = "lamp not-configured";
      els.twilioBadge.textContent = "Twilio: Not Configured";
    }
  }

  if (els.demoBadge) {
    if (state.demo_mode) {
      els.demoBadge.className = "lamp demo";
      els.demoBadge.textContent = "Mode: Demo (Simulated)";
    } else {
      els.demoBadge.className = "lamp real";
      els.demoBadge.textContent = "Mode: Live Twilio";
    }
  }

  setText(els.railAlertMode, state.demo_mode ? "Demo Mode (Simulated)" : "Live Twilio Carrier");
  setText(els.railLastEvent, state.event_time === "--:--" ? "No recent event" : state.event_time);

  if (els.commGateway) {
    setText(els.commGateway, state.demo_mode ? "Demo Simulator Gateway" : "Live Twilio Gateway");
  }

  if (els.demoModeInput) {
    els.demoModeInput.checked = state.demo_mode;
  }
  setInputValue(els.vehicleInput, state.vehicle_number);
  setInputValue(els.locationInput, state.location_text);

  applyTheme(state.mode);
  updateTimeline(state.mode);
  updateDispatchPanel(state);
  renderContacts(state.contacts);
  renderLogs(state.logs);
}

async function refresh() {
  try {
    const state = await api("/api/state");
    renderState(state);
  } catch (error) {
    console.error("Dashboard refresh error:", error);
  }
}

// Bind Emergency Action Buttons
document.querySelectorAll("[data-action]").forEach((button) => {
  button.addEventListener("click", () => postAction(button.dataset.action));
});

// Bind Settings Form (Garage Setup)
bind(els.settingsForm, "submit", async (event) => {
  event.preventDefault();
  try {
    await api("/api/settings", {
      method: "POST",
      body: JSON.stringify({
        vehicle_number: els.vehicleInput.value,
        location_text: els.locationInput.value,
        demo_mode: els.demoModeInput.checked
      })
    });
    if (els.saveFeedback) {
      els.saveFeedback.style.display = "inline";
      setTimeout(() => {
        if (els.saveFeedback) els.saveFeedback.style.display = "none";
      }, 3000);
    }
    await refresh();
  } catch (err) {
    console.error("Settings save error:", err);
  }
});

// Bind Contacts Table Edit Button
bind(els.contactsBody, "click", async (event) => {
  const button = event.target.closest("[data-edit]");
  if (!button || !els.contactDialog) return;
  try {
    const state = await api("/api/state");
    const index = Number(button.dataset.edit);
    const contact = state.contacts[index];
    if (!contact) return;
    els.contactIndex.value = String(index);
    els.contactName.value = contact.name;
    els.contactNumber.value = contact.number;
    els.contactDialog.showModal();
  } catch (err) {
    console.error("Contact edit dialog error:", err);
  }
});

bind(els.closeDialog, "click", () => els.contactDialog.close());

bind(els.contactForm, "submit", async (event) => {
  event.preventDefault();
  try {
    await api("/api/contact", {
      method: "POST",
      body: JSON.stringify({
        index: Number(els.contactIndex.value),
        name: els.contactName.value,
        number: els.contactNumber.value
      })
    });
    els.contactDialog.close();
    await refresh();
  } catch (err) {
    console.error("Contact form error:", err);
  }
});

// Start real-time telemetry polling
refresh();
setInterval(refresh, 1000);
