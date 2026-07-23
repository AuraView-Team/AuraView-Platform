# AuraView

**Real-Time Crowd Intelligence & Security Platform**

AuraView is a real-time crowd monitoring and security intelligence platform designed to help security personnel monitor crowd density, detect potential risks, and respond quickly to emerging situations. The platform combines computer vision, AI-powered analytics, real-time communication, and a dedicated mobile application to deliver actionable insights from live video streams.

It supports multiple video sources including webcams, RTSP cameras, and YouTube Live streams while providing live crowd analysis, predictive risk assessment, and instant notifications for security teams.

---

# Features

## Web Dashboard

### Real-Time Video Analytics
- Monitor live video feeds from webcams, RTSP/IP cameras, and YouTube Live streams.
- Detect people in real time using YOLO-based object detection models.

### Crowd Density Analysis
- Generate live crowd density information and spatial heatmaps.
- Visualize congestion across monitored locations.

### Predictive Risk Assessment
- Calculate crowd risk levels in real time.
- Classify conditions as **Safe**, **Warning**, or **Danger**.
- Forecast crowd growth for the next 1, 5, 10, and 15 minutes.

### Security Personnel Management
- Register and manage security personnel.
- Assign secure mobile login credentials.
- Manage authentication using Supabase.

---

## Security Guard Mobile Application

The companion mobile application enables field personnel to receive instant alerts and monitor system status.

### Features

- Instant push and local notifications during emergency situations.
- Secure mobile number and PIN-based authentication.
- Automatic WebSocket reconnection.
- Live connection status indicator.
- Location-based monitoring support.

---

# Technology Stack

## Backend
- Python 3.12
- FastAPI
- Uvicorn
- OpenCV
- PyTorch
- Ultralytics YOLOv8 / YOLOv5
- Scikit-Learn
- Pandas
- NumPy

## Real-Time Communication
- Python Socket.IO
- WebSockets

## Video Streaming
- yt-dlp

## Database & Authentication
- Supabase
- PostgreSQL

## Frontend
- HTML5
- CSS3
- Vanilla JavaScript
- Chart.js

## Mobile Application
- React Native
- Expo SDK 54
- Expo Notifications
- Socket.IO Client

---

# Project Structure

```text
AuraView/
│
├── backend/
├── aura-guard-app/
├── static/
├── templates/
├── models/
├── requirements.txt
├── cookies.txt
└── README.md
```

---

# Getting Started

## Prerequisites

Install the following before running the project.

- Python 3.12 (Python 3.9 or later supported)
- Node.js 18+
- npm
- Expo Go (Android/iOS)

---

# Environment Variables

Create a `.env` file in the project root.

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

---

# YouTube Live Stream Support

When using YouTube Live URLs as camera sources, `yt-dlp` requires a valid `cookies.txt` file.

## Generate cookies.txt

1. Install the **Get cookies.txt LOCALLY** extension for Chrome or Firefox.
2. Sign in to your YouTube account.
3. Export your cookies in **Netscape HTTP Cookie File** format.
4. Save the exported file as:

```text
AuraView/cookies.txt
```

---

# Running the Backend

Create a virtual environment (recommended):

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI server:

```bash
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser:

```text
http://localhost:8000
```

---

# Running the Mobile Application

Open another terminal.

```bash
cd aura-guard-app
npm install
npm start
```

Scan the QR code using the Expo Go application.

Configure the backend URL inside the app:

```text
http://<YOUR_LOCAL_IPV4_ADDRESS>:8000
```

Ensure that both the mobile device and the computer are connected to the same Wi-Fi network.

---

# License

This project is licensed under the **Apache License 2.0**.

See the `LICENSE` file for complete license details.
