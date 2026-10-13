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
    def _zerogpu_probe():
        return True

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

STATIC_DIR = BASE_DIR / "static"

def get_java_bin():
    # 1. Check if system java is already version 21+
    try:
        res = subprocess.run(["java", "-version"], capture_output=True, text=True)
        version_str = res.stderr or res.stdout
        if any(f'version "{v}' in version_str for v in ("21", "22", "23", "24")):
            return "java"
    except Exception:
        pass

    # 2. Check if local JRE 21 exists
    jre_dir = BASE_DIR / "bin" / "jre-21"
    for candidate in jre_dir.rglob("bin/java"):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)

    # 3. Download standalone Temurin JRE 21 (Linux x64)
    if sys.platform.startswith("linux"):
        print("📥 Downloading portable OpenJDK 21 JRE for OTP 2.6.0...")
        jre_tar = BASE_DIR / "bin" / "jre21.tar.gz"
        jre_url = "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.2%2B13/OpenJDK21U-jre_x64_linux_hotspot_21.0.2_13.tar.gz"
        jre_dir.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(jre_url, jre_tar)
        import tarfile
        with tarfile.open(jre_tar, "r:gz") as tar:
            tar.extractall(path=jre_dir)
        if jre_tar.exists():
            jre_tar.unlink()
        for candidate in jre_dir.rglob("bin/java"):
            if candidate.is_file():
                os.chmod(candidate, 0o755)
                print(f"✔ Java 21 portable JRE ready: {candidate}")
                return str(candidate)

    return "java"

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

    # 3. Check graph and resolve LFS pointer if needed
    graph_path = router_dir / "graph.obj"
    if not graph_path.exists() or graph_path.stat().st_size < 1000:
        print("📥 Resolving compiled transit graph via huggingface_hub...")
        try:
            from huggingface_hub import hf_hub_download
            import shutil
            downloaded = hf_hub_download(
                repo_id="Th3G3nt13man/istanbul-transit-core",
                filename="data/router/graph.obj",
                repo_type="space"
            )
            shutil.copyfile(downloaded, graph_path)
            print("✔ graph.obj (198 MB) resolved successfully!")
        except Exception as e:
            print(f"⚠️ Failed to auto-download graph.obj: {e}")

    # 4. Resolve Java 21 and launch OTP
    if graph_path.exists() and graph_path.stat().st_size > 1000:
        java_cmd = get_java_bin()
        print(f"🚀 Starting OpenTripPlanner on port 8080 with 4GB heap using {java_cmd}...")
        subprocess.Popen([
            java_cmd, "-Xmx4G", "-jar", str(otp_jar), "--load", str(router_dir)
        ])
        for i in range(45):
            try:
                with urllib.request.urlopen("http://localhost:8080/", timeout=1):
                    print("✔ OpenTripPlanner graph engine is ready!")
                    break
            except Exception:
                time.sleep(1)
    else:
        print("⚠️ NOTE: data/router/graph.obj not found locally or invalid.")

# Launch OTP in background daemon thread
threading.Thread(target=start_background_otp, daemon=True).start()

# Import Gradio and FastAPI dependencies
import gradio as gr
from fastapi.staticfiles import StaticFiles
from src.api.main import app as fastapi_app

# Define Gradio Blocks interface (ZeroGPU probe / engine fallback)
with gr.Blocks(title="Istanbul Transit Core", fill_height=True) as demo:
    gr.Markdown("# 🚆 Istanbul Transit Core - Engine Online")
    _probe_btn = gr.Button("ZeroGPU Probe", visible=False)
    _probe_btn.click(fn=_zerogpu_probe)

# Remove default static mount from router so Gradio can cleanly register at /gradio
fastapi_app.router.routes = [r for r in fastapi_app.router.routes if getattr(r, 'path', '') != '']

# Mount Gradio at /gradio
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

# Mount Static Web UI & PWA at "/" (Native zero-iframe Leaflet PWA with manifest.json & sw.js)
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

if __name__ == "__main__":
    print("🚀 Starting Istanbul Transit Core on Hugging Face Spaces (0.0.0.0:7860)...")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

