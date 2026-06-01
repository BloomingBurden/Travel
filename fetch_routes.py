import urllib.request, json

# Waypoints per phase as [lat, lon] (same as ROUTE_Px in turkey_map.html)
PHASES = {
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
    geo = rdp(geo, 0.0006)
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
