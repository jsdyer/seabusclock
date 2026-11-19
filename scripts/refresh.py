"""Extract scheduled service from the agency feed and preserve date exceptions."""
import argparse
import csv
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from io import BytesIO, TextIOWrapper
import json
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
URL = "https://gtfs-static.translink.ca/gtfs/google_transit.zip"

def rows(archive, name):
    with archive.open(name + ".txt") as stream:
        yield from csv.DictReader(TextIOWrapper(stream, encoding="utf-8-sig"))

def minute(value):
    h, m, s = map(int, value.split(":"))
    if s != 0:
        raise ValueError("Schedule gained sub-minute times")
    return h * 60 + m

def calendar(archive, start, end):
    services = defaultdict(set)
    for row in rows(archive, "calendar"):
        low, high = row["start_date"], row["end_date"]
        day = start
        while day <= end:
            stamp = day.strftime("%Y%m%d")
            if low <= stamp <= high and row[day.strftime("%A").lower()] == "1":
                services[day.isoformat()].add(row["service_id"])
            day += timedelta(days=1)
    for row in rows(archive, "calendar_dates"):
        day = datetime.strptime(row["date"], "%Y%m%d").date()
        if start <= day <= end:
            bag = services[day.isoformat()]
            if row["exception_type"] == "1":
                bag.add(row["service_id"])
            elif row["exception_type"] == "2":
                bag.discard(row["service_id"])
            else:
                raise ValueError("Unknown GTFS service exception")
    return {d:sorted(ids) for d,ids in sorted(services.items())}

def snapshot(archive):
    feed = next(rows(archive,"feed_info"))
    start, end = [datetime.strptime(feed[k],"%Y%m%d").date() for k in ("feed_start_date","feed_end_date")]
    services = calendar(archive,start,end)
    data = extract(archive)
    active = set(data["events"])
    if not active or not any(active.intersection(ids) for ids in services.values()):
        raise ValueError("No matching scheduled service")
    data.update(calendar={day:[i for i in ids if i in active] for day,ids in services.items()},
                start=start.isoformat(), end=end.isoformat(), version=feed["feed_version"],
                retrieved=datetime.now(timezone.utc).date().isoformat(), source=URL)
    return data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--feed",type=Path,help="Existing official GTFS ZIP for offline validation")
    args = parser.parse_args()
    raw = args.feed.read_bytes() if args.feed else urlopen(URL,timeout=100).read()
    with ZipFile(BytesIO(raw)) as archive:
        data = snapshot(archive)
    output = ROOT/"web/data"
    output.mkdir(parents=True,exist_ok=True)
    for file,obj in [("schedule",data),("status",{k:data[k] for k in ("start","end","version","retrieved")})]:
        stage = output/(file+".tmp")
        stage.write_text(json.dumps(obj,ensure_ascii=False,separators=(",",":"))+"\n")
        stage.replace(output/(file+".json"))

def extract(archive):
    route_ids = {r["route_id"] for r in rows(archive,"routes") if r["route_type"]=="4" and "seabus" in r["route_long_name"].lower()}
    trips = {r["trip_id"]:r for r in rows(archive,"trips") if r["route_id"] in route_ids}
    stops = {r["stop_id"]:r["stop_name"] for r in rows(archive,"stops")}
    crossings = defaultdict(list)
    for row in rows(archive,"stop_times"):
        if row["trip_id"] in trips:
            crossings[row["trip_id"]].append(row)
    events = defaultdict(list)
    names = set()
    for trip,items in crossings.items():
        dep,arr = sorted(items,key=lambda r:int(r["stop_sequence"]))
        origin = stops[dep["stop_id"]]
        terminal = next((term for term in ["Waterfront","Lonsdale Quay"] if term.lower() in origin.lower()),None)
        if not terminal:
            raise ValueError("Unknown SeaBus terminal: "+origin)
        names.add(terminal)
        events[trips[trip]["service_id"]].append([minute(dep["departure_time"]), minute(arr["arrival_time"]),terminal])
    if len(names)!=2: raise ValueError("Missing SeaBus direction")
    return {"events":{k:sorted(v) for k,v in events.items()}}

if __name__ == "__main__":
    main()
