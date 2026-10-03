from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os

from src.core.hybrid_router import hybrid_router
from src.core.search_engine import search_engine
from src.realtime.iett_client import iett_client
from src.config import BASE_DIR, STATIC_DIR, CORS_ORIGINS

os.makedirs(STATIC_DIR, exist_ok=True)

app = FastAPI(
    title="İstanbul Bağımsız Toplu Taşıma Motoru",
    description="Reklamsız, derin arama yapabilen ve canlı GPS telemetrisi destekleyen multimodal rota motoru",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=False if "*" in CORS_ORIGINS else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RouteRequest(BaseModel):
    from_lat: float = Field(..., description="Başlangıç Enlemi")
    from_lon: float = Field(..., description="Başlangıç Boylamı")
    to_lat: float = Field(..., description="Varış Enlemi")
    to_lon: float = Field(..., description="Varış Boylamı")
    prefer_modes: Optional[List[str]] = Field(None, description="Öncelikli ulaşım modları (FERRY, SUBWAY, METRO, MARMARAY, METROBUS, BUS)")
    avoid_modes: Optional[List[str]] = Field(None, description="Kaçınılacak modlar (BUS, FERRY, SUBWAY)")
    force_mode: Optional[str] = Field(None, description="Rotada kesinlikle bulunması zorunlu mod (FERRY, SUBWAY, BUS)")
    allow_minibus: bool = Field(False, description="Minibüs ve dolmuşları rotaya dahil et")
    target: str = Field("FASTEST", description="Optimizasyon hedefi (FASTEST, LEAST_TRANSFERS, LEAST_WALKING, SCENIC_WATER)")
    time_type: str = Field("DEPART_NOW", description="Kalkış/Varış türü (DEPART_NOW, DEPART_AT, ARRIVE_BY)")
    prefer_ferry: bool = Field(False, description="Vapur hatlarına öncelik ver (Geriye dönük uyumluluk)")
    force_ferry: bool = Field(False, description="Rotada mutlaka vapur kullanılsın (Geriye dönük uyumluluk)")
    num_itineraries: int = Field(4, description="Maksimum rota sayısı")
    time_str: Optional[str] = Field(None, description="Saat (HH:MM:SS)")
    date_str: Optional[str] = Field(None, description="Tarih (YYYY-MM-DD)")

POPULAR_HUBS = [
    {"id": "ist_havalimani", "name": "İstanbul Havalimanı (IST)", "lat": 41.2612, "lon": 28.7420, "type": "airport"},
    {"id": "saw_havalimani", "name": "Sabiha Gökçen Havalimanı (SAW)", "lat": 40.9086, "lon": 29.2846, "type": "airport"},
    {"id": "kadikoy", "name": "Kadıköy Rıhtım / Meydan", "lat": 40.9904, "lon": 29.0253, "type": "hub"},
    {"id": "besiktas", "name": "Beşiktaş İskele", "lat": 41.0422, "lon": 29.0067, "type": "hub"},
    {"id": "uskudar", "name": "Üsküdar Meydan / Marmaray", "lat": 41.0267, "lon": 29.0153, "type": "hub"},
    {"id": "eminonu", "name": "Eminönü Vapur & Tramvay", "lat": 41.0175, "lon": 28.9733, "type": "hub"},
    {"id": "taksim", "name": "Taksim Meydanı / Metro", "lat": 41.0370, "lon": 28.9850, "type": "hub"},
    {"id": "mecidiyekoy", "name": "Mecidiyeköy Metrobüs & M2", "lat": 41.0667, "lon": 28.9936, "type": "hub"},
    {"id": "halicioglu", "name": "Halıcıoğlu Metrobüs", "lat": 41.0485, "lon": 28.9455, "type": "hub"},
    {"id": "yenikapi", "name": "Yenikapı Marmaray & Metro", "lat": 41.0055, "lon": 28.9505, "type": "hub"},
    {"id": "ayrilik_cesmesi", "name": "Ayrılık Çeşmesi Marmaray & M4", "lat": 41.0001, "lon": 29.0303, "type": "hub"},
    {"id": "bostanci", "name": "Bostancı İskele & Marmaray", "lat": 40.9525, "lon": 29.0945, "type": "hub"},
    {"id": "bakirkoy", "name": "Bakırköy İskele & Meydan", "lat": 40.9780, "lon": 28.8720, "type": "hub"},
    {"id": "sogutlucesme", "name": "Söğütlüçeşme Marmaray & Metrobüs", "lat": 40.9915, "lon": 29.0376, "type": "hub"},
    {"id": "zincirlikuyu", "name": "Zincirlikuyu Metrobüs", "lat": 41.0682, "lon": 29.0118, "type": "hub"},
]

@app.get("/api/search")
def search_places(q: str = Query(..., min_length=2, description="Arama terimi")):
    """Instant search for Istanbul transit stops, metro stations, piers, and landmarks."""
    return {"results": search_engine.search(q, limit=8)}

@app.get("/api/hubs")
def get_hubs():
    """Returns popular transport hubs in Istanbul."""
    return {"hubs": POPULAR_HUBS}

@app.get("/api/plan")
def plan_route_get(
    from_lat: float,
    from_lon: float,
    to_lat: float,
    to_lon: float,
    target: str = "FASTEST",
    allow_minibus: bool = False,
    prefer_modes: Optional[str] = None,
    avoid_modes: Optional[str] = None,
    force_mode: Optional[str] = None,
    num_itineraries: int = 4
):
    pref_list = [m.strip() for m in prefer_modes.split(",")] if prefer_modes else None
    avoid_list = [m.strip() for m in avoid_modes.split(",")] if avoid_modes else None
    return hybrid_router.plan(
        from_lat=from_lat,
        from_lon=from_lon,
        to_lat=to_lat,
        to_lon=to_lon,
        prefer_modes=pref_list,
        avoid_modes=avoid_list,
        force_mode=force_mode,
        allow_minibus=allow_minibus,
        target=target,
        num_itineraries=num_itineraries
    )

@app.post("/api/plan")
def plan_route(req: RouteRequest):
    """
    Computes Pareto-optimal multimodal journeys across Istanbul,
    enriched with intermediate stops, estimated fare, carbon savings, and live GPS telemetry.
    """
    result = hybrid_router.plan(
        from_lat=req.from_lat,
        from_lon=req.from_lon,
        to_lat=req.to_lat,
        to_lon=req.to_lon,
        prefer_modes=req.prefer_modes,
        avoid_modes=req.avoid_modes,
        force_mode=req.force_mode,
        allow_minibus=req.allow_minibus,
        target=req.target,
        time_type=req.time_type,
        date_str=req.date_str,
        time_str=req.time_str,
        num_itineraries=req.num_itineraries,
        prefer_ferry=req.prefer_ferry,
        force_ferry=req.force_ferry
    )
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Routing error"))
    return result

@app.get("/api/live/buses/{line_code}")
def get_live_buses_for_line(line_code: str):
    """Returns active vehicles with live GPS, fleet ID, and direction for a line."""
    buses = iett_client.get_live_buses(line_code)
    return {
        "line_code": line_code.upper(),
        "active_count": len(buses),
        "buses": buses
    }

# Mount static web UI
if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
