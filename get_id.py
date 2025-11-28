import requests
KEY = "API_KEY_HERE"
STATION_API = "https://api.ekispert.jp/v1/json/station"
station_list =["飯田橋", "東京", "渋谷", "秋葉原", "浅草", "上野", "池袋", "六本木", "銀座", "新宿", "赤羽橋"]
def as_list(x):
    return x if isinstance(x, list) else ([] if x is None else [x])

def station_code(name: str) -> str:
    r = requests.get(STATION_API, params={"key": KEY, "name": name, "limit": 1}, timeout=20)
    r.raise_for_status()
    point = r.json().get("ResultSet", {}).get("Point")
    point = point[0] if isinstance(point, list) and point else point

    code = (point or {}).get("Station", {}).get("code") or (point or {}).get("Station", {}).get("Code")
    if not code:
        raise ValueError(f"Station not found / no code: {name}")
    return str(code)

for i in station_list:
    print(station_code(i))