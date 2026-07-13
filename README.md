# ??? AuraView — Real-Time Crowd Intelligence & Security Platform

AuraView is an advanced, real-time crowd monitoring, density estimation, and automated security alerting platform. It combines state-of-the-art computer vision (YOLOv8/YOLOv5), high-performance asynchronous web frameworks (FastAPI), low-latency WebSocket communication (Socket.IO), and a dedicated mobile portal (React Native / Expo) to empower security personnel with instant threat awareness and spatial crowd analytics.

---

## ? Key Features

### ??? Intelligent Web Dashboard
* **Real-Time Video Analytics:** Connect multi-source live video feeds via **YouTube Live Streams**, **RTSP network cameras**, or local **Webcams**.
* **AI Crowd Density & Heatmaps:** Instantaneous person detection and clustering algorithms (DBSCAN/Linear Regression) with visual spatial congestion heatmaps.
* **Dynamic Risk Scoring & Predictions:** Real-time calculation of crowd risk levels (SAFE, WARNING, DANGER) and predictive forecasting of crowd buildup over 1, 5, 10, and 15-minute intervals.
* **Security Guard Management:** Integrated admin portal to register security personnel, assign 10-digit mobile login IDs, and manage site access via Supabase.

### ?? Dedicated Security Guard Mobile App (ura-guard-app)
* **Instantaneous Push & Local Alerts:** Real-time emergency acoustic and visual alarms triggered via WebSockets whenever crowd density exceeds custom safety thresholds.
* **Secure Numeric Portal:** ATM-style simplified login (Mobile Number + 4-Digit PIN) specifically tailored for high-speed field operations.
* **Live Connection Status:** Continuous connection health indicator with automatic reconnect capabilities and localized site filtering.

---

## ??? Tech Stack

* **Backend API & AI Pipeline:** Python 3.12, FastAPI, Uvicorn, OpenCV, PyTorch, Ultralytics (YOLOv8/YOLOv5), Scikit-Learn, Pandas, NumPy.
* **Real-Time Streaming:** Python Socket.IO, WebSockets, yt-dlp (for live media extraction).
* **Database & Authentication:** Supabase (PostgreSQL, Service Role Auth).
* **Web Dashboard:** Pure HTML5, CSS3 (Glassmorphism & dark-mode design system), Vanilla JavaScript, Chart.js.
* **Mobile Application:** React Native, Expo (SDK 54), Expo Notifications, Socket.IO Client.

---

## ?? Getting Started & Setup Guide

### 1. Prerequisites
Ensure you have the following installed on your operating system:
* **Python 3.9+** (Python 3.12 recommended)
* **Node.js 18+ & npm**
* **Expo Go App** installed on your physical Android/iOS smartphone

---

### 2. Environment Variables Setup (.env)
Create a .env file in the root project directory (Aura-View-main) and add your Supabase credentials:
\\\env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_secret_key
\\\

---

### 3. Important: YouTube Live Streams Setup (cookies.txt)
If you plan to use **YouTube Live Stream URLs** as camera inputs, yt-dlp requires a valid cookies.txt file to authenticate and bypass YouTube bot protections. Without this file, YouTube video extraction will fail.

#### How to generate cookies.txt:
1. Install the **"Get cookies.txt LOCALLY"** extension for [Chrome](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/ccjipodfaomnaogalnkchocokhhg) or [Firefox](https://addons.mozilla.org/en-US/firefox/addon/get-cookies-txt-locally/).
2. Open your web browser and log in to [YouTube.com](https://www.youtube.com).
3. Click the extension icon and export your cookies in **Netscape HTTP Cookie File format**.
4. Save the exported file as cookies.txt directly inside the root directory (Aura-View-main/cookies.txt).

---

### 4. Running the Backend & Web Dashboard
Open your terminal in the root directory (Aura-View-main) and run:

\\\ash
# Create and activate a virtual environment (Optional but recommended)
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install required Python dependencies
pip install -r requirements.txt

# Launch the FastAPI server bound to all network interfaces (0.0.0.0)
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
\\\
* Access the Web Dashboard by navigating to: **http://localhost:8000**

---

### 5. Running the Security Guard Mobile App (ura-guard-app)
Open a **NEW terminal window**, navigate to the mobile app folder, and launch the Expo bundler:

\\\ash
cd aura-guard-app

# Install Node modules
npm install

# Start the Expo development bundler
npm start
\\\
* Press **\\** to open the app on an Android Emulator, OR open the **Expo Go** app on your physical mobile phone and scan the QR Code displayed in the terminal.
* In the Mobile App Login Screen, enter your **Laptop's Local IPv4 Address** as the Backend URL:
  \\\	ext
  http://<YOUR_LAPTOP_WIFI_IPV4_ADDRESS>:8000
  \\\
  *(Note: Your physical phone and laptop must be connected to the **same Wi-Fi network**).*

---

## ?? License
This project is licensed under the MIT License. See the LICENSE file for details.
