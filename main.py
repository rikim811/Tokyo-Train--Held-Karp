# pip install requests
import requests

KEY = "test_ba3CYJYscMP"
COURSE_API = "https://api.ekispert.jp/v1/json/search/course/extreme"

station_list = {
    "Iidabashi": 22507,
    "Tokyo": 22828,
    "Shibuya": 22715,
    "Akihabara": 22492,
    "Asakusa": 22495,
    "Ueno": 22528,
    "Ikebukuro": 22513,
    "Roppongi": 23049,
    "Ginza": 22641,
    "Shinjuku": 22741,
    "Akabanebashi": 29341,
}

def as_list(x):
    return x if isinstance(x, list) else ([] if x is None else [x])

def parse_course(course: dict):
    route = course.get("Route", {})
    minutes = sum(int(route.get(k, "0")) for k in ("timeOnBoard", "timeWalk", "timeOther"))
    transfers = int(route.get("transferCount", "0"))

    fare = None
    for p in as_list(course.get("Price")):
        if isinstance(p, dict) and p.get("kind") == "FareSummary" and p.get("Oneway") is not None:
            fare = int(p["Oneway"])
            break

    lines = [ln["Name"] for ln in as_list(route.get("Line")) if isinstance(ln, dict) and ln.get("Name")]
    return {"minutes": minutes, "transfers": transfers, "fare": fare, "lines": lines}

def get_routes(frm_key: str, to_key: str, date=20251128, time=1200, answer_count=20):
    frm = station_list[frm_key]
    to = station_list[to_key]
    via = f"{frm}:{to}"

    r = requests.get(
        COURSE_API,
        params={
            "key": KEY,
            "viaList": via,
            "date": int(date),
            "time": int(time),
            "sort": "time",
            "answerCount": min(int(answer_count), 20),
            "searchType": "departure",
        },
        timeout=20
    )
    r.raise_for_status()

    courses = as_list(r.json().get("ResultSet", {}).get("Course"))
    routes = [parse_course(c) for c in courses if isinstance(c, dict)]
    return [x for x in routes if x["fare"] is not None]

if __name__ == "__main__":
    routes = get_routes("Iidabashi", "Shibuya", date=20251128, time=1200, answer_count=20)
    if not routes:
        raise SystemExit("No routes found.")

    print("CHEAPEST:", min(routes, key=lambda x: (x["fare"], x["minutes"], x["transfers"])))
    print("FASTEST:", min(routes, key=lambda x: (x["minutes"], x["transfers"], x["fare"])))
    print("FEWEST_TRANSFERS:", min(routes, key=lambda x: (x["transfers"], x["minutes"], x["fare"])))
