#!/usr/bin/env python3
"""
app.py
================================================================================
Hugging Face Spaces (Gradio SDK / ZeroGPU) Entrypoint for Istanbul Transit Core
================================================================================
"""

import os
import sys
import time
import subprocess
import threading
import urllib.request
from pathlib import Path

# 0. ZeroGPU Probe (Satisfies Hugging Face ZeroGPU runtime check if space runs on ZeroGPU)
try:
    import spaces
    @spaces.GPU
    def _zerogpu_probe():
        """Satisfies Hugging Face ZeroGPU startup probe."""
        return True
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

STATIC_DIR = BASE_DIR / "static"

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

# Import Gradio and FastAPI dependencies
import gradio as gr
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from src.api.main import app as fastapi_app

# Define Gradio Blocks interface embedding the interactive Leaflet web UI
with gr.Blocks(title="Istanbul Transit Core", fill_height=True) as demo:
    gr.HTML("""
    <iframe src="/map" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; border: none; z-index: 9999;" allow="geolocation"></iframe>
    """)

# Mount vendor assets directly onto Gradio's internal FastAPI app
demo.app.mount("/vendor", StaticFiles(directory=str(STATIC_DIR / "vendor")), name="vendor")

# Route for rendering the interactive map HTML
@demo.app.get("/map")
def get_map():
    return FileResponse(str(STATIC_DIR / "index.html"))

# Forward all /api/ endpoints from our core router into Gradio's FastAPI app
for route in fastapi_app.routes:
    if getattr(route, "path", "").startswith("/api"):
        demo.app.routes.insert(0, route)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    print(f"🚀 Starting Istanbul Transit Core on 0.0.0.0:{port}...")
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        css="footer {visibility: hidden}"
    )
