"""Refresh a compact statistical extract from the latest published TSPR CSV."""
from collections import defaultdict
import csv
from datetime import datetime, timezone
from html.parser import HTMLParser
import io
import json
import math
from pathlib import Path
import re
from urllib.parse import urljoin
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
INDEX = "https://www.translink.ca/plans-and-projects/strategies-plans-and-guidelines/managing-the-transit-network"

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.matches = []
    def handle_starttag(self, tag, attrs):
        href = dict(attrs).get("href","")
        if tag == "a" and (match := re.search(PATTERN,href,re.I)):
            self.matches.append((int(match[1]),urljoin(INDEX,href)))

def number(value):
    if value.strip().upper() in ("","NULL","N/A"): return None
    n = float(value)
    if not math.isfinite(n) or n < 0: raise ValueError("Unexpected negative or nonfinite value")
    return round(n,4)

def main():
    links = Links()
    links.feed(urlopen(INDEX,timeout=50).read().decode())
    edition, source = max(links.matches)
    raw = urlopen(source,timeout=80).read().decode("utf-8-sig")
    entries, years, n = extract(csv.DictReader(io.StringIO(raw)))
    if edition not in years or len(years)<2 or n<100:
        raise ValueError("Incomplete TSPR edition")
    now = datetime.now(timezone.utc).date().isoformat()
    obj = {"edition":edition,"years":sorted(years),"source":source,"retrieved":now,"entries":entries}
    status = {"retrieved":now,"records":n,"edition":str(edition),"start":str(min(years)),"end":str(max(years))}
    folder = ROOT/"web/data"
    folder.mkdir(exist_ok=True,parents=True)
    for name, content in ((OUT,obj),(OUT+"-status",status)):
        tmp = folder/(name+".tmp")
        tmp.write_text(json.dumps(content,separators=(",",":"),ensure_ascii=False)+"\n")
        tmp.replace(folder/(name+".json"))

PATTERN = r"tspr(\d{4})_seabus_capvolpkload_[^/?]+\.csv"
OUT = "seabus"

def extract(rows):
    groups, years, n = {}, set(), 0
    for r in rows:
        year, hour = int(r["SeasonYear"]),int(r["Hourly"])
        direction = r["Direction"]
        if direction not in ("Northbound","Southbound") or hour not in range(24):
            raise ValueError("Unknown direction or clock hour")
        key = "|".join([str(year),r["Season"],r["day_type"]])
        group = groups.setdefault(key,{}).setdefault(direction,{})
        if str(hour) in group: raise ValueError("Duplicate service hour")
        group[str(hour)] = number(r["AvgDailyVolume"])
        years.add(year)
        n += 1
    if not all(set(v)=={"Northbound","Southbound"} for v in groups.values()):
        raise ValueError("Missing SeaBus direction")
    return groups, years, n

if __name__ == "__main__":
    main()
