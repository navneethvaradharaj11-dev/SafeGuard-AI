# SafeGuard AI - Smart Accident Detection & Response System

<p align="center">
  <img src="static/logo.png" alt="SafeGuard AI logo" width="180" />
</p>

**© 2026 Navneeth Varadharaj. All rights reserved.**

A compact Python-based demonstration of an end-to-end accident detection and emergency response workflow. SafeGuard AI provides both a browser dashboard and a Tkinter desktop interface to simulate real-time accident detection and emergency escalation.

**Live demo:** https://accident-detection-response-system.vercel.app

## Highlights

- ⚡ Lightweight, single-repo demo for presentations and testing
- 🌐 Browser-based dashboard plus Tkinter desktop UI
- 📡 Simulated real-time accident events and automated escalation
- 📞 Configurable workflow: driver response → SMS → acknowledgement → voice calls
- 🔗 Twilio REST integration for real SMS and voice calls (optional)
- 🛡️ Demo mode to safely demonstrate behavior without sending real messages

## Repository Layout

```text
.
├── accident_ui.py              # Tkinter desktop dashboard
├── web_dashboard.py            # Browser dashboard server
├── twilio.py                   # Twilio REST helper and message builders
├── static/
│   ├── app.js                  # Dashboard client behavior
│   └── styles.css              # Dashboard styling
├── templates/
│   ├── index.html              # Main dashboard page
│   ├── garage_setup.html       # Setup view
│   └── service_bay.html        # Service/diagnostics view
├── requirements.txt            # Python dependencies
├── .env.example                # Example environment variables
├── LICENSE                     # MIT License
└── .github/workflows/ci.yml    # CI smoke tests (syntax + imports)
```

## Requirements

- Python 3.10+
- Optional: a Twilio account and credentials to send real SMS/voice calls

## Installation

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Configuration

1. Copy the example environment file and update values:

```bash
cp .env.example .env
# or on Windows (PowerShell)
# copy .env.example .env
```

2. Edit `.env` and provide your Twilio credentials and phone numbers if you want to enable real notifications.

### Example (.env)

```text
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+14155552671
TWILIO_TO_NUMBER=+919876543210
DASHBOARD_DEMO_MODE=true
```

**Important:** Do not commit `.env` or any real credentials into source control. This repository intentionally ignores `.env`.

## Running the Project

### Web Dashboard (default host: http://127.0.0.1:8080)

```bash
python web_dashboard.py
```

**Options:**
- Prevent automatic browser open: `python web_dashboard.py --no-browser`
- Use a different port: `python web_dashboard.py --port 8125`

### Tkinter Desktop Dashboard

```bash
python accident_ui.py
```

## Notification Modes

- **Demo mode** (default when credentials are missing): Simulates SMS/calls and is safe for demos.
- **Live mode**: Enable real SMS/voice by providing Twilio credentials in `.env` and disabling demo mode in the dashboard.

## Emergency Workflow

1. System monitors for events in normal mode.
2. Trigger an accident simulation from the dashboard.
3. Alarm activates; a 30-second driver response timer starts.
4. If the driver confirms safety, the workflow resets.
5. If the timer expires, SMS alerts are sent to configured emergency contacts.
6. A 15-second acknowledgement timer begins for contacts to confirm receipt.
7. If no acknowledgement is received, the system escalates to automated voice calls via Twilio.

## CI / Testing

The repository includes a minimal GitHub Actions workflow that runs on push and pull requests. The workflow:

- Installs Python and dependencies
- Runs a syntax check (compileall)
- Imports the main modules as a smoke test

This keeps the CI fast while catching syntax errors and broken imports.

## Security & Safety Notes

- Never commit real Twilio credentials, API keys, or private data to the repository.
- Verify recipient phone numbers and test with demo mode before enabling live notifications.
- **This project is a demonstration system only** — do not rely on it for real emergency handling without extensive testing, validation, and appropriate infrastructure.

## Contributing

Contributions, bug reports, and improvements are welcome! Please:
- Open issues or pull requests
- Describe the change and reasoning
- For larger changes, open an issue first to discuss the approach

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

**© 2026 Navneeth Varadharaj. All rights reserved.**

SafeGuard AI™ is a demonstration project. Use at your own risk.
