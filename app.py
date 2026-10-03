#!/usr/bin/env python3
"""
app.py
================================================================================
Hugging Face Spaces (Gradio SDK) Entrypoint for Istanbul Transit Core
================================================================================
This script:
1. Automatically downloads the official OpenTripPlanner 2.6.0 shaded jar if missing.
2. Starts OpenTripPlanner on background port 8080.
3. Launches our full FastAPI & Leaflet interactive transit map on port 7860
   via Gradio/Uvicorn, completely free on Hugging Face Spaces.
================================================================================
"""

import os
import sys
import time
import subprocess
import threading
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

def start_background_otp():
    otp_jar = BASE_DIR / "bin" / "otp-2.6.0-shaded.jar"
    router_dir = BASE_DIR / "data" / "router"
    
    # 1. Check if OTP is already healthy
    try:
        with urllib.request.urlopen("http://localhost:8080/", timeout=1):
            print("✔ OpenTripPlanner is already active on port 8080.")
            return
    except Exception:
        pass

    # 2. Download OTP jar if not present
    otp_jar.parent.mkdir(parents=True, exist_ok=True)
    if not otp_jar.exists():
        print("📥 Downloading OpenTripPlanner 2.6.0 shaded JAR from Maven Central...")
        url = "https://repo1.maven.org/maven2/org/opentripplanner/otp/2.6.0/otp-2.6.0-shaded.jar"
        urllib.request.urlretrieve(url, otp_jar)
        print("✔ OTP JAR download complete!")

    # 3. Check graph and launch OTP
    graph_path = router_dir / "graph.obj"
    if graph_path.exists():
        print("🚀 Starting OpenTripPlanner on port 8080 with 4GB heap...")
        subprocess.Popen([
            "java", "-Xmx4G", "-jar", str(otp_jar), "--load", str(router_dir)
        ])
        for i in range(35):
            try:
                with urllib.request.urlopen("http://localhost:8080/", timeout=1):
                    print("✔ OpenTripPlanner graph engine is ready!")
                    break
            except Exception:
                time.sleep(1)
    else:
        print("⚠️ NOTE: data/router/graph.obj not found locally.")

# Launch OTP in background daemon thread
threading.Thread(target=start_background_otp, daemon=True).start()

# Import our FastAPI application
from src.api.main import app as fastapi_app

try:
    import gradio as gr
    # Create Gradio interface embedding our full Leaflet interactive map
    with gr.Blocks(title="Istanbul Transit Core", fill_height=True, css="footer {visibility: hidden}") as demo:
        gr.HTML("""
        <iframe src="/static/index.html" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; border: none; z-index: 9999;" allow="geolocation"></iframe>
        """)

    # Mount Gradio onto our FastAPI application
    app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")
except ImportError:
    app = fastapi_app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    print(f"🚀 Starting Istanbul Transit Core Web Gateway on 0.0.0.0:{port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
