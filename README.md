# SeaBus Clock

[Open SeaBus Clock](https://coolcode.ca/seabusclock/) to find the busiest SeaBus hours by direction and see the scheduled gap between sailings.

<!-- coolcode:guide -->
Compare fall weekday volumes in each direction, then select a terminal and service date to see the scheduled wait after a missed sailing.
<!-- /coolcode:guide -->

## Reading the records

The hourly profile uses AvgDailyVolume from the newest TSPR seasonal SeaBus hourly CSV. A missing hour remains missing. The schedule uses GTFS route type 4 and the SeaBus route name, both terminal stop times, weekly calendars and holiday exceptions. After-midnight times use the original service date and appear on the corresponding civil date. The first next-day sailing and its following gap are included in late-night searches. Date selection is bounded by the retrieved feed. Service disruptions and vehicle positions are outside this schedule. The seasonal averages are historical and independent of the sailing date selected.

## Sources and maintenance

[TransLink performance review](https://www.translink.ca/plans-and-projects/strategies-plans-and-guidelines/managing-the-transit-network) and [static schedule and terms](https://www.translink.ca/about-us/doing-business-with-translink/app-developer-resources/gtfs/gtfs-data). The published snapshot includes retrieval dates in UTC and its source coverage. The page filters the downloaded data on the device and does not transmit selections.

Daily timetable · Monthly performance check. Run `python3 scripts/refresh.py` and `python3 scripts/refresh_profile.py`. Automatic updates validate before publishing. Run `node --test tests/*.test.mjs`, `python3 -m unittest discover -s tests -v` and `python3 scripts/build.py`.

Route and arrival data used in this product or service is provided by permission of TransLink. TransLink assumes no responsibility for the accuracy or currency of the Data used in this product or service.

<!-- schedule-reliability -->
## Schedule reliability

Public GitHub repositories can have scheduled workflows disabled after 60 days of inactivity. A separate weekly [schedule guard](.github/workflows/schedule-guard.yml) calls GitHub's enable-workflow API for an explicit list of refresh workflows and itself. It can restore workflows disabled for inactivity, preserves manually disabled workflows, and runs independently of collection failures.

This is an interim mitigation, not a scheduling guarantee: GitHub does not document active-workflow renewal as a permanent exemption, and scheduled runs can be delayed or dropped. A scheduler on our own Linux server is the planned independent trigger. The guard does not collect data, create dummy commits, or change source/check timestamps; successful collection and published data freshness still need monitoring.
<!-- /schedule-reliability -->
