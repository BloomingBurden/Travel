import urllib.request, json

# Waypoints per leg as [lat, lon] (same as ROUTE_Px in turkey_map.html).
# Map phase ids: P4 = Этап 1 (ЕКБ→Ереван), P5 = Этап 2 (Ереван-база day-trips),
# P1 = Этап 3 (Ереван→Анталия), P2 = Этап 4 (Анталия-база), P3 = Этап 5 (на запад).
# Per-leg RDP epsilon (degrees): coarser on the long Russia leg.
EPS = {"ROUTE_P1": 0.0006, "ROUTE_P2": 0.0006, "ROUTE_P3": 0.0006,
       "ROUTE_P4": 0.0025, "ROUTE_P5": 0.0010}
PHASES = {
    "ROUTE_P4": [  # ЕКБ → Самара → Волгоград → Владикавказ → Верхний Ларс → Тбилиси → Садахло → Ереван
        [56.8389,60.6057],[54.7388,55.9721],[53.1959,50.1002],[51.5331,46.0342],
        [48.7080,44.5133],[46.3080,44.2558],[44.0486,43.0594],[43.0241,44.6814],
        [42.6573,44.6430],[41.7151,44.8271],[41.2086,44.8316],[40.1792,44.4991],
    ],
    "ROUTE_P5": [  # Ереван day-trips: Гарни/Гегард, Хор Вирап/Арени/Нораванк, Севан/Дилижан, Эчмиадзин
        [40.1792,44.4991],[40.1122,44.7300],[40.1550,44.8180],[40.1792,44.4991],
        [39.8783,44.5764],[39.7167,45.1956],[39.6847,45.2331],[40.1792,44.4991],
        [40.5670,45.0110],[40.7406,44.8628],[40.1792,44.4991],[40.1620,44.2910],
        [40.1792,44.4991],
    ],
    "ROUTE_P1": [
        [40.1792,44.4991],[41.115,43.473],[41.640,43.000],[41.325,42.940],
        [40.601,43.097],[40.507,43.572],[40.601,43.097],
        [39.905,41.267],[38.643,34.829],[37.874,32.493],[36.887,30.702],
    ],
    "ROUTE_P2": [
        [36.887,30.702],[37.062,30.474],[36.887,30.702],
        [36.961,30.855],[36.939,31.172],[36.887,30.702],
        [36.523,30.556],[36.887,30.702],
    ],
    "ROUTE_P3": [
        [36.887,30.702],[36.398,30.478],[36.202,29.640],
        [36.552,29.115],[36.622,29.113],[36.461,29.246],
        [37.923,29.121],[37.940,27.342],[38.419,27.129],
    ],
}

BASE = "https://router.project-osrm.org/route/v1/driving/"

# Ramer-Douglas-Peucker on [lon,lat] points. epsilon in degrees (~0.0006 ≈ 65m)
def rdp(points, eps):
    if len(points) < 3:
        return points
    def perp(p, a, b):
        (x, y), (x1, y1), (x2, y2) = p, a, b
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            return ((x - x1) ** 2 + (y - y1) ** 2) ** 0.5
        t = ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))
        px, py = x1 + t * dx, y1 + t * dy
        return ((x - px) ** 2 + (y - py) ** 2) ** 0.5
    dmax, idx = 0, 0
    for i in range(1, len(points) - 1):
        d = perp(points[i], points[0], points[-1])
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        left = rdp(points[:idx + 1], eps)
        right = rdp(points[idx:], eps)
        return left[:-1] + right
    return [points[0], points[-1]]

def dedupe(pts):
    out = []
    for p in pts:
        if not out or out[-1] != p:
            out.append(p)
    return out

def fetch(name, pts):
    pts = dedupe(pts)
    coords = ";".join(f"{lon},{lat}" for lat, lon in pts)
    url = f"{BASE}{coords}?overview=full&geometries=geojson"
    with urllib.request.urlopen(url, timeout=90) as r:
        data = json.loads(r.read())
    if data.get("code") != "Ok":
        raise SystemExit(f"{name}: OSRM error {data.get('code')} {data.get('message','')}")
    geo = data["routes"][0]["geometry"]["coordinates"]  # [lon,lat]
    geo = rdp(geo, EPS.get(name, 0.0006))
    latlon = [[round(lat,5), round(lon,5)] for lon, lat in geo]
    dist = data["routes"][0]["distance"]/1000
    print(f"// {name}: {len(latlon)} pts, {dist:.0f} km", flush=True)
    return name, latlon

results = {}
for name, pts in PHASES.items():
    n, ll = fetch(name, pts)
    results[n] = ll

with open("routes_geometry.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False)
print("WROTE routes_geometry.json", flush=True)
