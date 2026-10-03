import urllib.request
import json
from datetime import datetime

q = """
{
  plan(
    from: {lat: 41.0396, lon: 28.8944}
    to: {lat: 40.9920, lon: 29.1120}
    date: "2026-10-03"
    time: "14:00:00"
    numItineraries: 4
    transportModes: [{mode: WALK}, {mode: TRANSIT}]
  ) {
    itineraries {
      startTime
      endTime
      duration
      waitingTime
      legs {
        mode
        startTime
        endTime
        duration
        route { shortName }
        from { name }
        to { name }
      }
    }
  }
}
"""

rq = urllib.request.Request("http://localhost:8080/otp/routers/default/index/graphql",
    data=json.dumps({"query": q}).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(rq) as res:
    data = json.load(res)

itins = data["data"]["plan"]["itineraries"]
target_ts = datetime.strptime("2026-10-03 14:00:00", "%Y-%m-%d %H:%M:%S").timestamp() * 1000

print(f"Total itineraries found: {len(itins)}")
for i, it in enumerate(itins):
    legs = it["legs"]
    transit_legs = [l for l in legs if l["mode"] != "WALK"]
    dur_min = it["duration"] // 60
    initial_curb_wait = int((it["startTime"] - target_ts) / 60000)
    real_elapsed = int((it["endTime"] - target_ts) / 60000)

    print(f"=== Option {i+1} ===")
    print(f"  OTP Reported Duration: {dur_min} min")
    print(f"  Initial Curb Wait Time: {initial_curb_wait} min")
    print(f"  Real Door-to-Door (Moovit Style): {real_elapsed} min")
    for j in range(len(legs) - 1):
        l1 = legs[j]
        l2 = legs[j+1]
        gap_sec = (l2["startTime"] - l1["endTime"]) / 1000.0
        l1_name = f"{l1['mode']} {(l1.get('route') or {}).get('shortName','')}".strip()
        l2_name = f"{l2['mode']} {(l2.get('route') or {}).get('shortName','')}".strip()
        print(f"    {l1_name} ends {datetime.fromtimestamp(l1['endTime']/1000).strftime('%H:%M:%S')} -> GAP: {gap_sec:.0f}s ({gap_sec/60:.1f}m) -> {l2_name} starts {datetime.fromtimestamp(l2['startTime']/1000).strftime('%H:%M:%S')}")
    print()
