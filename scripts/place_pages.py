"""Render native city examples from the same public snapshots as the interactive tool."""
from html import escape
import json
import re

from search_metadata import add_search_metadata


from datetime import date, timedelta


def load_sources(stage):
    return tuple(json.loads((stage / "data" / name).read_text()) for name in ("schedule.json", "seabus.json"))


def clock(minutes):
    return f"{minutes // 60 % 24:02d}:{minutes % 60:02d}" + (" next day" if minutes >= 1440 else "")


def case_content(sources, terminal, direction):
    schedule, ridership = sources
    day = max(schedule["start"], min(schedule["retrieved"][:10], schedule["end"]))
    # Include departures after midnight that belong to the previous service day.
    previous = date.fromisoformat(day) - timedelta(days=1)
    times = sorted((depart + offset, arrive + offset)
                   for service_day, offset in ((previous.isoformat(), -1440), (day, 0))
                   for group in schedule["calendar"].get(service_day, [])
                   for depart, arrive, origin in schedule["events"][group]
                   if origin == terminal and 480 <= depart + offset < 1440)
    attrs = {"terminal": terminal, "schedule-date": day}
    text = f'<p><strong>{escape(terminal)} departures from 08:00 Pacific on {day}</strong></p>'
    if times:
        text += "<ul>" + "".join(f"<li>Depart {clock(depart)} · arrive {clock(arrive)} · {arrive-depart} minutes scheduled</li>" for depart, arrive in times[:3]) + "</ul>"
        if len(times) > 1:
            text += f"<p>After the first sailing shown, the next scheduled departure is {times[1][0]-times[0][0]} minutes later.</p>"
    else:
        text += "<p>No departures appear in this timetable after 08:00 for the example date.</p>"
    year = max(ridership["years"])
    values = ridership["entries"].get(f"{year}|Fall|MF", {}).get(direction, {})
    measured = [(int(hour), volume) for hour, volume in values.items() if isinstance(volume, (int, float))]
    if measured:
        hour, volume = min(measured, key=lambda pair: (-pair[1], pair[0]))
        text += f"<p>In fall {year}, the busiest reported {direction.lower()} weekday hour began at {hour:02d}:00, averaging {volume:,.0f} passengers.</p>"
    text += '<p><a href="#terminal">Change date or time</a> · <a href="' + escape(schedule["source"], quote=True) + '">TransLink GTFS timetable (ZIP)</a> · <a href="' + escape(ridership["source"], quote=True) + '">Hourly passenger data (CSV)</a></p>'
    return attrs, text


CASES = [
    ('waterfront-to-lonsdale-quay', 'Waterfront to Lonsdale Quay SeaBus Schedule', 'See morning SeaBus departures from downtown Vancouver to North Vancouver. Compare the time between crossings and the historical northbound ridership peak.', 'Waterfront', 'Northbound'),
    ('lonsdale-quay-to-waterfront', 'Lonsdale Quay to Waterfront SeaBus Schedule', 'Find morning sailings from North Vancouver to downtown Vancouver. Compare the scheduled crossing time, the gap after a missed boat and the historical southbound ridership peak.', 'Lonsdale Quay', 'Southbound'),
]


def publish_pages(stage, template, tool):
    sources = load_sources(stage)
    entries = []
    for slug, title, description, *fields in CASES:
        filename = slug + ".html"
        attributes, evidence = case_content(sources, *fields)
        attributes["use-case"] = slug
        state = " ".join(f'data-{key}="{escape(str(value), quote=True)}"' for key, value in attributes.items())
        page = template.replace("<body ", "<body " + state + " ", 1)
        page = re.sub(r"<title>.*?</title>", lambda _: "<title>" + escape(title) + " · CoolCode</title>", page, count=1)
        page = re.sub(r"(<h1[^>]*>).*?</h1>", lambda m: m[1] + escape(title) + "</h1>", page, count=1, flags=re.S)
        page = re.sub(r'(<meta name="description" content=")[^"]*', lambda m: m[1] + escape(description, quote=True), page, count=1)
        example = '<section class="place-evidence" aria-label="Published example"><p>' + escape(description) + '</p>' + evidence + '</section>'
        page = page.replace("<!-- place-example -->", example).replace("<!-- place-links -->", '<a href="./">Open ' + escape(tool["title"]) + '</a>')
        info = {**tool, "title": title, "description": description, "url": tool["url"] + filename}
        (stage / filename).write_text(add_search_metadata(page, info), encoding="utf-8")
        entries.append('<a href="./' + filename + '">' + escape(title) + '</a>')
    home = template.replace("<!-- place-example -->", "").replace("<!-- place-links -->", " ".join(entries))
    (stage / "index.html").write_text(add_search_metadata(home, tool), encoding="utf-8")
