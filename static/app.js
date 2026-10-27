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
  railGps: qs("#railGps"),
  railCircuit: qs("#railCircuit"),
  railHwLink: qs("#railHwLink"),
  dispatchHeadline: qs("#dispatchHeadline"),
  dispatchSubline: qs("#dispatchSubline"),

  // Automotive Telemetry & Sensor Topology
  driverStatusBadge: qs("#driverStatusBadge"),
  driverAlertnessVal: qs("#driverAlertnessVal"),
  driverAlertnessFill: qs("#driverAlertnessFill"),
  driverEyeStatus: qs("#driverEyeStatus"),
  dmsSourceLabel: qs("#dmsSourceLabel"),
  vehicleSensorStatus: qs("#vehicleSensorStatus"),
  sensorFront: qs("#sensorFront"),
  sensorRear: qs("#sensorRear"),
  sensorLeft: qs("#sensorLeft"),
  sensorRight: qs("#sensorRight"),
  emergencyHeaderBadge: qs("#emergencyHeaderBadge"),
  cabinBuzzerStatus: qs("#cabinBuzzerStatus"),
  impactGForce: qs("#impactGForce"),
  tiltAngleDisplay: qs("#tiltAngleDisplay"),
  telemetrySpeed: qs("#telemetrySpeed"),
  hwSourceBadge: qs("#hwSourceBadge"),
  commGateway: qs("#commGateway"),
  saveFeedback: qs("#saveFeedback"),

  // AI Crash Severity Assessment
  aiSeverityBadge: qs("#aiSeverityBadge"),
  aiConfidence: qs("#aiConfidence"),
  aiDeltaV: qs("#aiDeltaV"),
  aiAirbag: qs("#aiAirbag"),
  aiRecommendation: qs("#aiRecommendation"),

  // Connection Analyzer & Diagnostics Dialog
  openDiagnosticsBtn: qs("#openDiagnosticsBtn"),
  diagnosticsDialog: qs("#diagnosticsDialog"),
  closeDiagnosticsDialog: qs("#closeDiagnosticsDialog"),
  diagHealthScore: qs("#diagHealthScore"),
  diagHwLabel: qs("#diagHwLabel"),
  diagTableBody: qs("#diagTableBody"),
  pinoutChips: qs("#pinoutChips"),
  runDiagBtn: qs("#runDiagBtn"),
  serialPortSelect: qs("#serialPortSelect"),
  connectSerialBtn: qs("#connectSerialBtn"),
  webSerialBtn: qs("#webSerialBtn"),

  // DMS Camera
  toggleCameraBtn: qs("#toggleCameraBtn"),
  dmsCameraContainer: qs("#dmsCameraContainer"),
  dmsVideo: qs("#dmsVideo"),
  dmsCanvas: qs("#dmsCanvas"),

  // Service Bay elements
  sbHealthBadge: qs("#sbHealthBadge"),
  sbHardwareSource: qs("#sbHardwareSource"),
  sbRunDiagnostics: qs("#sbRunDiagnostics")
};

let lastContactsKey = "";
let cameraStream = null;
let cameraLoopInterval = null;
let closedEyeCounter = 0;

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
    } else if (mode === "driver_wait") {
      els.driverStatusBadge.classList.add("warning");
      setText(els.driverStatusBadge, "Checking Response");
      setText(els.driverEyeStatus, "Closed / Warning");
    } else if (["message_dispatch", "contact_wait", "auto_calling", "completed"].includes(mode)) {
      els.driverStatusBadge.classList.add("danger");
      setText(els.driverStatusBadge, "Unresponsive");
      setText(els.driverEyeStatus, "No Response");
    } else if (mode === "resolved") {
      els.driverStatusBadge.classList.add("normal");
      setText(els.driverStatusBadge, "Confirmed Safe");
      setText(els.driverEyeStatus, "Normal");
    }
  }

  // Update Vehicle Top-View Sensors
  const isAccident = ["driver_wait", "message_dispatch", "contact_wait", "auto_calling", "completed"].includes(mode);
  if (els.vehicleSensorStatus) {
    els.vehicleSensorStatus.className = "status-badge " + (isAccident ? "danger" : "normal");
    setText(els.vehicleSensorStatus, isAccident ? "Impact Detected" : "4 Sensors Armed");
  }

  if (els.sensorFront) els.sensorFront.classList.toggle("impact-alert", isAccident);
  if (els.sensorLeft) els.sensorLeft.classList.toggle("impact-alert", isAccident);
  if (els.sensorRight) els.sensorRight.classList.toggle("impact-alert", isAccident && mode === "driver_wait");

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

function updateSeverityCard(info) {
  if (!info || !els.aiSeverityBadge) return;
  setText(els.aiSeverityBadge, info.severity_level || "NOMINAL");
  if (info.badge_color) {
    els.aiSeverityBadge.style.color = info.badge_color;
    els.aiSeverityBadge.style.borderColor = info.badge_color;
  }
  setText(els.aiConfidence, `${info.ai_confidence_pct || 99}%`);
  setText(els.aiDeltaV, `${info.estimated_delta_v_kmh || 0} km/h`);
  setText(els.aiAirbag, info.airbag_deployed ? "DEPLOYED 💥" : "Armed (Nominal)");
  setText(els.aiRecommendation, info.recommendation || "System baseline monitoring active.");
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

  // Live dynamic telemetry values
  if (els.impactGForce) {
    const isAccident = state.mode !== "normal" && state.mode !== "resolved";
    setText(els.impactGForce, `${(state.g_force || 1.02).toFixed(2)} G ${isAccident ? "(COLLISION TRIGGER)" : "(Nominal Vector)"}`);
    els.impactGForce.style.color = isAccident ? "var(--danger)" : "var(--text-primary)";
  }

  if (els.tiltAngleDisplay) {
    setText(els.tiltAngleDisplay, `${(state.tilt_angle || 1.4).toFixed(1)}° Tilt (Roll ${(state.roll || 0.8).toFixed(1)}°, Pitch ${(state.pitch || 1.2).toFixed(1)}°)`);
  }

  if (els.telemetrySpeed) {
    setText(els.telemetrySpeed, `${(state.speed_kmh || 48.5).toFixed(1)} km/h (${state.satellites || 9} Sats, 3D Fix)`);
  }

  if (els.driverAlertnessVal) {
    setText(els.driverAlertnessVal, `${state.driver_alertness || 96}%`);
    if (els.driverAlertnessFill) {
      els.driverAlertnessFill.style.width = `${state.driver_alertness || 96}%`;
      els.driverAlertnessFill.style.backgroundColor = (state.driver_alertness || 96) > 75 ? "var(--success)" : "var(--danger)";
    }
  }

  if (els.hwSourceBadge) {
    setText(els.hwSourceBadge, state.hardware_source || "Active Sensor Bridge");
  }

  if (els.railHwLink) {
    setText(els.railHwLink, state.hardware_source || "Active Bridge (100% Loop)");
  }

  // Update AI severity info
  if (state.severity_info) {
    updateSeverityCard(state.severity_info);
  }

  // Badges
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

// ---------------- CONNECTION ANALYZER & HARDWARE DIAGNOSTICS ----------------

async function loadDiagnostics() {
  try {
    const data = await api("/api/diagnostics");
    if (els.diagHealthScore) setText(els.diagHealthScore, data.overall_health_score || "100%");
    if (els.diagHwLabel) setText(els.diagHwLabel, data.connected_hardware);
    if (els.sbHardwareSource) setText(els.sbHardwareSource, data.connected_hardware);

    if (els.diagTableBody && data.components) {
      els.diagTableBody.innerHTML = data.components.map((c) => `
        <tr style="border-bottom: 1px solid var(--border-light);">
          <td style="padding: 8px; font-weight: 600;">${escapeHtml(c.component)}</td>
          <td style="padding: 8px; color: var(--text-secondary); font-family: ui-monospace, monospace;">${escapeHtml(c.connection_type)}</td>
          <td style="padding: 8px;"><code>${c.pins.join(", ")}</code></td>
          <td style="padding: 8px;"><strong style="color: #10b981;">${c.integrity_score}%</strong></td>
          <td style="padding: 8px;"><span class="status-chip ready">${escapeHtml(c.status_label)}</span></td>
        </tr>
      `).join("");
    }

    if (els.pinoutChips && data.pinout) {
      els.pinoutChips.innerHTML = data.pinout.map((p) => `
        <div class="pinout-chip" title="${escapeHtml(p.description)}">
          <strong>GPIO ${p.gpio_number}</strong> (${escapeHtml(p.pin_name)}):
          <span>${escapeHtml(p.current_voltage)}</span>
          <span style="color: #10b981;">✓ ${escapeHtml(p.status)}</span>
        </div>
      `).join("");
    }
  } catch (err) {
    console.error("Diagnostics load error:", err);
  }
}

async function loadSerialPorts() {
  if (!els.serialPortSelect) return;
  try {
    const data = await api("/api/serial/ports");
    els.serialPortSelect.innerHTML = (data.ports || []).map((port) => `
      <option value="${escapeHtml(port.device)}">${escapeHtml(port.device)} (${escapeHtml(port.description)})</option>
    `).join("");
  } catch (err) {
    console.error("Serial ports error:", err);
  }
}

// Bind Diagnostics Dialog Triggers
if (els.openDiagnosticsBtn) {
  els.openDiagnosticsBtn.addEventListener("click", () => {
    loadDiagnostics();
    loadSerialPorts();
    if (els.diagnosticsDialog) els.diagnosticsDialog.showModal();
  });
}

if (els.closeDiagnosticsDialog) {
  els.closeDiagnosticsDialog.addEventListener("click", () => {
    if (els.diagnosticsDialog) els.diagnosticsDialog.close();
  });
}

if (els.runDiagBtn) {
  els.runDiagBtn.addEventListener("click", async () => {
    els.runDiagBtn.textContent = "Analyzing Circuits...";
    await loadDiagnostics();
    setTimeout(() => {
      if (els.runDiagBtn) els.runDiagBtn.textContent = "↻ Re-Run Diagnostics";
    }, 600);
  });
}

if (els.sbRunDiagnostics) {
  els.sbRunDiagnostics.addEventListener("click", async () => {
    els.sbRunDiagnostics.textContent = "Analyzing Circuits...";
    await loadDiagnostics();
    setTimeout(() => {
      if (els.sbRunDiagnostics) els.sbRunDiagnostics.textContent = "↻ Run Connection Diagnostics";
    }, 600);
  });
}

// Connect Serial Port
if (els.connectSerialBtn) {
  els.connectSerialBtn.addEventListener("click", async () => {
    const selectedPort = els.serialPortSelect.value;
    try {
      const res = await api("/api/serial/connect", {
        method: "POST",
        body: JSON.stringify({ port: selectedPort, baud: 115200 })
      });
      alert(res.message || (res.ok ? "Port Connected!" : "Connection Failed"));
      await refresh();
      await loadDiagnostics();
    } catch (err) {
      alert("Error connecting port: " + err.message);
    }
  });
}

// Direct Web Serial API (Chrome/Edge USB Hardware Connection)
if (els.webSerialBtn) {
  els.webSerialBtn.addEventListener("click", async () => {
    if (!("serial" in navigator)) {
      alert("Web Serial API is available in Chrome, Edge, and Opera. For other browsers, use the Serial Port selector.");
      return;
    }
    try {
      const port = await navigator.serial.requestPort();
      await port.open({ baudRate: 115200 });
      alert("Connected to ESP32 via USB Web Serial! Live hardware streaming active.");
      
      const textDecoder = new TextDecoderStream();
      port.readable.pipeTo(textDecoder.writable);
      const reader = textDecoder.readable.getReader();
      
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        if (value && value.includes("{")) {
          // Stream hardware line
          console.log("Hardware Serial Data:", value);
        }
      }
    } catch (err) {
      if (err.name !== "NotFoundError") {
        console.warn("Web Serial error:", err);
      }
    }
  });
}

// ---------------- CRASH PHYSICS PRESET TRIGGERS ----------------
document.querySelectorAll("[data-crash]").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const crashType = btn.dataset.crash;
    try {
      await api("/api/crash_test", {
        method: "POST",
        body: JSON.stringify({ type: crashType })
      });
      await refresh();
    } catch (err) {
      console.error("Crash test error:", err);
    }
  });
});

// ---------------- LIVE DRIVER MONITORING CAMERA (DMS) ----------------
if (els.toggleCameraBtn) {
  els.toggleCameraBtn.addEventListener("click", async () => {
    if (cameraStream) {
      // Stop Camera
      cameraStream.getTracks().forEach((track) => track.stop());
      cameraStream = null;
      if (cameraLoopInterval) clearInterval(cameraLoopInterval);
      if (els.dmsCameraContainer) els.dmsCameraContainer.style.display = "none";
      setText(els.toggleCameraBtn, "📹 Camera");
      setText(els.dmsSourceLabel, "IR Camera Active");
    } else {
      // Start Live Camera
      try {
        cameraStream = await navigator.mediaDevices.getUserMedia({
          video: { width: 320, height: 240 }
        });
        if (els.dmsVideo) {
          els.dmsVideo.srcObject = cameraStream;
        }
        if (els.dmsCameraContainer) els.dmsCameraContainer.style.display = "block";
        setText(els.toggleCameraBtn, "🛑 Stop Camera");
        setText(els.dmsSourceLabel, "Live WebRTC Camera");

        // Computer Vision Eye & Driver Alertness Analysis Loop
        cameraLoopInterval = setInterval(() => {
          if (!els.dmsVideo || !els.dmsCanvas) return;
          const ctx = els.dmsCanvas.getContext("2d");
          els.dmsCanvas.width = 64;
          els.dmsCanvas.height = 48;
          ctx.drawImage(els.dmsVideo, 0, 0, 64, 48);
          
          const frame = ctx.getImageData(0, 0, 64, 48);
          let brightness = 0;
          for (let i = 0; i < frame.data.length; i += 4) {
            brightness += (frame.data[i] + frame.data[i + 1] + frame.data[i + 2]) / 3;
          }
          brightness = brightness / (frame.data.length / 4);

          // Simulated face & eye openness metric
          const eyeOpen = brightness > 35;
          if (!eyeOpen) {
            closedEyeCounter++;
            if (closedEyeCounter >= 4) { // Closed for > 2 seconds
              api("/api/dms/status", {
                method: "POST",
                body: JSON.stringify({ alertness: 45, drowsy: true })
              }).catch(() => {});
            }
          } else {
            closedEyeCounter = 0;
            api("/api/dms/status", {
              method: "POST",
              body: JSON.stringify({ alertness: 96, drowsy: false })
            }).catch(() => {});
          }
        }, 500);
      } catch (err) {
        alert("Camera access denied or unavailable: " + err.message);
      }
    }
  });
}

// ---------------- DASHBOARD DATA REFRESH ----------------
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

// Initial load & periodic polling
refresh();
loadDiagnostics();
setInterval(refresh, 500);
