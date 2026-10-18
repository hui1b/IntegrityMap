import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_JSON = ROOT / "data.json"
DATA_JS = ROOT / "data.js"

USER_AGENT = "NationalIntegrityCultureMap/1.0 (+https://example.com)"


def clean_query(value):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = text.replace("（", "(").replace("）", ")").replace("《", "").replace("》", "")
    text = re.sub(r"\s*\([^)]*\)", "", text)
    return text.strip(" ,.-_/·")


def build_queries(point):
    school = clean_query(point.get("schoolName"))
    title = clean_query(point.get("title"))
    province = clean_query(point.get("province"))
    address = clean_query(point.get("address"))
    candidates = []
    for candidate in [
        address,
        f"{school} {title} {province}" if school and title and province else None,
        f"{school} {title}" if school and title else None,
        f"{school} {province}" if school and province else None,
        school,
        title,
    ]:
        if candidate and candidate not in candidates:
            candidates.append(candidate)
    return candidates


def fetch_nominatim(query):
    params = {
        "q": query,
        "format": "jsonv2",
        "limit": "1",
        "addressdetails": "1",
    }
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            if isinstance(payload, list) and payload:
                item = payload[0]
                return float(item["lat"]), float(item["lon"])
    except Exception:
        return None
    return None


def geocode_point(point):
    if point.get("lng") not in (None, "") and point.get("lat") not in (None, ""):
        return point

    for query in build_queries(point):
        if not query:
            continue
        result = fetch_nominatim(query)
        if result:
            lat, lon = result
            point["lat"] = lat
            point["lng"] = lon
            print(f"OK -> {point.get('id')} :: {query} :: ({lat}, {lon})")
            return point
        time.sleep(0.7)

    print(f"MISS -> {point.get('id')} :: {point.get('address')}")
    return point


def main():
    with DATA_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)

    points = data.get("points", [])
    count = 0
    for point in points:
        geocode_point(point)
        count += 1

    with DATA_JSON.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    js_payload = "window.MAP_DATA = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"
    DATA_JS.write_text(js_payload, encoding="utf-8")

    geocoded = sum(1 for p in points if p.get("lng") not in (None, "") and p.get("lat") not in (None, ""))
    print(f"Total points: {len(points)}")
    print(f"Geocoded points: {geocoded}")
    print(f"Saved to {DATA_JSON} and {DATA_JS}")


if __name__ == "__main__":
    main()
