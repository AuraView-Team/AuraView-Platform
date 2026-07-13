import os
import asyncio
import fastapi
import socketio
import uvicorn
import cv2
import torch
import yt_dlp
import numpy as np
import time
from fastapi import Request, HTTPException, Body
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from supabase import create_client

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.cluster import DBSCAN

# =========================
# ENV & CONFIG
# =========================
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

YOLO_MODEL_NAME = os.getenv("YOLO_MODEL_NAME", "yolov5s") # Faster for presentation
FRAME_SKIP = int(os.getenv("FRAME_SKIP", "5"))
RESIZE_WIDTH = int(os.getenv("RESIZE_WIDTH", "640"))

# ✅ MOBILE APP ALERT CONFIG

# =========================
# APP INIT
# =========================
app = fastapi.FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app.mount("/ws", socketio.ASGIApp(sio, socketio_path="/ws"))

supabase_admin = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# =========================
# GLOBAL STATE (SINGLE CAMERA)
# =========================
current_stream = {
    "active": False,
    "site_id": None,
    "type": None,
    "value": None,
    "threshold": 10,
    "train_interval": 1.0,  
    "last_train_time": 0.0, 
    "last_sms_time": 0.0,  
    "frame": None,
    "heatmap_layer": None,
    "trend": 0.0,
    "history": [],
    "stop": True
}
HEATMAP_ENABLED = False
SMS_COOLDOWN = 120 # ✅ Send SMS only once every 120 seconds (2 mins) to avoid spam

# =========================
# YOLO LOAD
# =========================
print("🧠 Loading YOLO model...")
model = torch.hub.load("ultralytics/yolov5", YOLO_MODEL_NAME, pretrained=True, trust_repo=True)
model.classes = [0] 
model.conf = 0.4    

# =========================
# HELPERS
# =========================
def resolve_status(count: int, threshold: int) -> str:
    if count >= threshold: return "DANGER"
    if count >= threshold * 0.6: return "MODERATE"
    return "SAFE"

def open_capture(source_type: str, source_value):
    if source_type == "webcam":
        try: idx = int(source_value) if str(source_value).strip() else 0
        except ValueError: idx = 0
        return cv2.VideoCapture(idx)

    if source_type == "youtube":
        val = str(source_value).strip()
        if val == "0" or len(val) < 5: return cv2.VideoCapture(0)
        try:
            ydl_opts = {"format": "best", "noplaylist": True, "quiet": True} 
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(val, download=False)
                return cv2.VideoCapture(info.get("url"), cv2.CAP_FFMPEG)
        except: return None
    return cv2.VideoCapture(str(source_value), cv2.CAP_FFMPEG)

def compute_clusters(centers, eps=60, min_samples=2):
    if len(centers) == 0: return 0, 0, 0.0
    X = np.array(centers, dtype=np.float32)
    if len(X) < 2: return 1, 1, 0.15
    db = DBSCAN(eps=eps, min_samples=min_samples).fit(X)
    labels = db.labels_
    unique = [l for l in set(labels) if l != -1]
    if not unique: return len(centers), 1, min(1.0, len(centers) / 20.0)
    cluster_sizes = [int(np.sum(labels == k)) for k in unique]
    return len(unique), max(cluster_sizes), min(1.0, (max(cluster_sizes) / max(1, len(centers))) * 1.8)

def compute_risk_score(count, clusters, largest_cluster, threshold):
    if threshold <= 0: threshold = 10
    cluster_threshold = max(5, int(threshold * 0.6))
    score = (0.45 * min(1.0, count / threshold)) + (0.35 * min(1.0, largest_cluster / cluster_threshold)) + (0.20 * min(1.0, clusters / 8.0))
    return int(max(0, min(100, score * 100)))

# SMS Logic removed in favor of Mobile App Push Notifications
# =========================
# ⏱️ AUTO-TRAINER BACKGROUND TASK
# =========================
async def auto_trainer():
    """Timer-based Auto Training Logic"""
    while True:
        await asyncio.sleep(2) 
        if current_stream["active"] and current_stream["train_interval"] > 0:
            now = time.time()
            if (now - current_stream["last_train_time"]) >= (current_stream["train_interval"] * 60):
                if len(current_stream["history"]) > 5:
                    try:
                        print(f"🤖 Training model after {current_stream['train_interval']} minutes of data collection...")
                        df = pd.DataFrame(current_stream["history"], columns=["ts", "count"])
                        df["minutes"] = (df["ts"] - df["ts"].min()) / 60.0
                        
                        model_lr = LinearRegression().fit(df[["minutes"]].values, df["count"].values)
                        current_stream["trend"] = float(model_lr.coef_[0])
                        current_stream["last_train_time"] = now 
                        print(f"✅ Training Complete! New Trend: {current_stream['trend']:.2f}")
                    except Exception as e:
                        print("Auto-Trainer Error:", e)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(auto_trainer())

# =========================
# API ENDPOINTS
# =========================
@app.get("/")
async def home():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f: return HTMLResponse(f.read())
    return {"message": "Backend running"}

@app.get("/config")
async def get_config():
    return {"threshold": current_stream["threshold"], "cluster_threshold": max(5, int(current_stream["threshold"] * 0.6)), "heatmap": HEATMAP_ENABLED}

@app.post("/set_heatmap")
async def set_heatmap(payload: dict = Body(...)):
    global HEATMAP_ENABLED
    HEATMAP_ENABLED = payload.get("enabled", False)
    return {"success": True, "heatmap": HEATMAP_ENABLED}

@app.post("/set_threshold")
async def set_threshold(payload: dict = Body(...)):
    th = int(payload.get("threshold", 10))
    current_stream["threshold"] = th
    return {"success": True, "threshold": th, "cluster_threshold": max(5, int(th * 0.6))}

@app.post("/setup_organization")
async def setup_organization(payload: dict = Body(...)):
    user_id = payload.get("user_id")
    company_name = payload.get("company_name")
    site_name = payload.get("site_name")
    if not user_id or not company_name or not site_name:
        return {"success": False, "message": "Missing parameters"}
    
    if supabase_admin:
        try:
            company_res = supabase_admin.table("companies").select("id").ilike("name", company_name).execute()
            if company_res.data and len(company_res.data) > 0:
                company_id = company_res.data[0]["id"]
            else:
                new_comp = supabase_admin.table("companies").insert({"name": company_name}).execute()
                company_id = new_comp.data[0]["id"]
            
            new_site = supabase_admin.table("sites").insert({"company_id": company_id, "name": site_name}).execute()
            site_id = new_site.data[0]["id"]
            
            supabase_admin.table("site_admins").insert({"user_id": user_id, "site_id": site_id}).execute()
            
            return {"success": True, "site_id": site_id, "company_id": company_id}
        except Exception as e:
            return {"success": False, "message": f"Setup error: {str(e)}"}
            
    return {"success": False, "message": "Supabase not configured"}

@app.post("/guard_login")
async def guard_login(payload: dict = Body(...)):
    guard_id = str(payload.get("guard_id", "")).strip()
    pin = str(payload.get("pin", "")).strip()
    if not guard_id or not pin:
        return {"success": False, "message": "Missing credentials"}
    
    if supabase_admin:
        try:
            res = supabase_admin.table("guard_devices").select("*").ilike("guard_id", guard_id).eq("pin", pin).execute()
            if res.data and len(res.data) > 0:
                fcm_token = payload.get("fcm_token")
                if fcm_token:
                    supabase_admin.table("guard_devices").update({"fcm_token": fcm_token}).eq("id", res.data[0]["id"]).execute()
                return {"success": True, "guard": res.data[0]}
        except Exception as e:
            return {"success": False, "message": f"Database error: {str(e)}"}
    
    return {"success": False, "message": "Invalid ID or PIN"}

@app.post("/set_source")
async def set_source(payload: dict = Body(...)):
    global current_stream
    
    current_stream["stop"] = True
    await asyncio.sleep(0.5)

    interval = float(payload.get("train_interval", 1.0))

    current_stream = {
        "active": True,
        "site_id": payload.get("site_id"),
        "type": payload.get("type", "youtube"),
        "value": payload.get("value"),
        "threshold": int(payload.get("threshold", 10)),
        "train_interval": interval,
        "last_train_time": time.time(),
        "last_sms_time": 0.0,
        "frame": None,
        "heatmap_layer": None,
        "trend": 0.0,
        "history": [],
        "stop": False
    }
    
    asyncio.create_task(camera_loop())
    return {"success": True}

@sio.on("join_site")
async def handle_join_site(sid, data):
    site_id = data.get("site_id")
    if site_id:
        sio.enter_room(sid, site_id)
        print(f"Client {sid} joined site {site_id}")

async def frame_generator():
    while True:
        if current_stream["active"] and current_stream["frame"] is not None:
            ok, encoded = cv2.imencode(".jpg", current_stream["frame"])
            if ok: yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + bytearray(encoded) + b"\r\n")
        await asyncio.sleep(0.03)

@app.get("/video_feed")
async def video_feed_stream():
    return StreamingResponse(frame_generator(), media_type="multipart/x-mixed-replace;boundary=frame")

# =========================
# SINGLE CAMERA LOOP
# =========================
async def camera_loop():
    global HEATMAP_ENABLED
    
    cap = open_capture(current_stream["type"], current_stream["value"])
    if not cap: return
    frame_counter = 0

    while not current_stream["stop"]:
        try:
            ok, frame = cap.read()
            if not ok:
                await asyncio.sleep(0.1)
                continue

            h, w = frame.shape[:2]
            scale = RESIZE_WIDTH / w
            resized = cv2.resize(frame, (int(w * scale), int(h * scale)))
            frame_counter += 1

            if frame_counter % FRAME_SKIP == 0:
                centers = []
                processed_frame = resized.copy()

                if model:
                    results = model(resized)
                    dets = results.xyxy[0].cpu().numpy() if len(results.xyxy) > 0 else np.empty((0, 6))
                    for d in dets: centers.append((int((d[0]+d[2])/2), int((d[1]+d[3])/2)))
                    results.render()
                    processed_frame = results.ims[0].copy()
                
                person_count = len(centers)
                cam_th = current_stream["threshold"]
                
                current_stream["history"].append((time.time(), person_count))
                if len(current_stream["history"]) > 600: current_stream["history"].pop(0) 
                
                cluster_count, largest_cluster, c_score = compute_clusters(centers)
                status = resolve_status(person_count, cam_th)
                c_thresh = max(5, int(cam_th * 0.6))
                c_alert = largest_cluster >= c_thresh
                r_score = compute_risk_score(person_count, cluster_count, largest_cluster, cam_th)
                future_prediction = int(max(0, person_count + (current_stream["trend"] * 5)))
                
                # ✅ TRIGGER MOBILE APP ALERT
                if status == "DANGER":
                    now = time.time()
                    if (now - current_stream["last_sms_time"]) > SMS_COOLDOWN:
                        current_stream["last_sms_time"] = now
                        site_id = current_stream.get("site_id")
                        room_id = site_id if site_id else None
                        await sio.emit("security_alert", {
                            "count": int(person_count),
                            "threshold": cam_th,
                            "timestamp": now,
                            "message": f"🚨 EMERGENCY: Crowd size is {person_count} (Limit: {cam_th})!"
                        }, room=room_id)
                        print(f"📱 Mobile App Alert Sent! Crowd: {person_count}/{cam_th}")

                if HEATMAP_ENABLED:
                    if current_stream["heatmap_layer"] is None:
                        current_stream["heatmap_layer"] = np.zeros_like(processed_frame, dtype=np.float32)
                    temp_heat = np.zeros_like(processed_frame, dtype=np.float32)
                    for cx, cy in centers: cv2.circle(temp_heat, (cx, cy), 40, (0, 0, 255), -1)
                    current_stream["heatmap_layer"] = cv2.addWeighted(current_stream["heatmap_layer"], 0.95, temp_heat, 0.05, 0)
                    heatmap_uint8 = cv2.convertScaleAbs(current_stream["heatmap_layer"])
                    processed_frame = cv2.addWeighted(processed_frame, 0.6, heatmap_uint8, 0.8, 0)

                current_stream["frame"] = processed_frame

                site_id = current_stream.get("site_id")
                room_id = site_id if site_id else None
                await sio.emit("broadcast_data", {
                    "count": int(person_count),
                    "prediction": future_prediction,
                    "threshold": cam_th,
                    "trend_per_min": float(current_stream["trend"]),
                    "alert_status": status,
                    "cluster_count": int(cluster_count),
                    "largest_cluster": largest_cluster,
                    "congestion_score": c_score,
                    "risk_score": int(r_score),
                    "cluster_alert": c_alert,
                    "cluster_threshold": c_thresh,
                    "heatmap_enabled": HEATMAP_ENABLED
                }, room=room_id)
            await asyncio.sleep(0.01)
        except Exception as e:
            await asyncio.sleep(0.5)
            
    if cap: cap.release()

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)