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
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from src.api.main import app as fastapi_app

# Define Gradio Blocks interface embedding the interactive Leaflet web UI
with gr.Blocks(title="Istanbul Transit Core", fill_height=True) as demo:
    gr.HTML("""
    <iframe src="/map" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; border: none; z-index: 9999;" allow="geolocation"></iframe>
    """)
    _probe_btn = gr.Button("ZeroGPU Probe", visible=False)
    _probe_btn.click(fn=_zerogpu_probe)

# Ensure localhost bypasses any proxies for Gradio local URL check
os.environ["no_proxy"] = "localhost,127.0.0.1,0.0.0.0"
os.environ["NO_PROXY"] = "localhost,127.0.0.1,0.0.0.0"

# 1. Mount static and vendor assets directly on demo.app
demo.app.mount("/vendor", StaticFiles(directory=str(STATIC_DIR / "vendor")), name="vendor")
demo.app.mount("/icons", StaticFiles(directory=str(STATIC_DIR / "icons")), name="icons")
demo.app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# 2. Map & PWA endpoints
@demo.app.get("/map")
def get_map():
    return FileResponse(str(STATIC_DIR / "index.html"))

@demo.app.get("/manifest.json")
def get_manifest():
    return FileResponse(str(STATIC_DIR / "manifest.json"), media_type="application/manifest+json")

@demo.app.get("/sw.js")
def get_sw():
    return FileResponse(
        str(STATIC_DIR / "sw.js"),
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"}
    )

# 3. Forward core FastAPI routes into demo.app
for route in fastapi_app.routes:
    if getattr(route, "path", "").startswith("/api"):
        demo.app.routes.insert(0, route)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    print(f"🚀 Starting Istanbul Transit Core on port {port}...")
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        show_error=True
    )
