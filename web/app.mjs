import "./harbour.mjs";
import { chooseDate, clock, mins } from "./schedule.mjs";
import { by, row, read } from "./ui.mjs";
import { sailings } from "./model.mjs";
try {
  const data = await read("schedule"),
    date = by("date");
  date.min = data.start;
  date.max = data.end;
  const preset = document.body.dataset;
  if (preset.terminal) by("terminal").value = preset.terminal;
  date.value = preset.scheduleDate >= data.start && preset.scheduleDate <= data.end
    ? preset.scheduleDate : chooseDate(data);
  by("edition").textContent =
    "Schedule " +
    data.start +
    " – " +
    data.end +
    " · retrieved " +
    data.retrieved;
  function draw() {
    by("sailrows").replaceChildren();
    if (
      !date.value ||
      date.value < data.start ||
      date.value > data.end ||
      !by("time").value
    ) {
      by("finding").textContent =
        "Choose a date within the published timetable and a departure time.";
      return;
    }
    const list = sailings(
      data,
      date.value,
      by("terminal").value,
      mins(by("time").value),
    );
    by("finding").textContent = list.length
      ? "Next scheduled departure " +
        clock(list[0][0]) +
        ". " +
        (list[1]
          ? "The following sailing is " +
            (list[1][0] - list[0][0]) +
            " minutes later."
          : "No following sailing in the available timetable.")
      : "No remaining departures in this date and next-day timetable.";
    by("sailrows").replaceChildren(
      ...list
        .filter(
          ([departure], index) =>
            departure < 1440 || index === 0 || index < list.length - 1,
        )
        .map(([dep, arr], i) =>
          row([
            clock(dep),
            clock(arr),
            list[i + 1] ? list[i + 1][0] - dep + " min" : "—",
          ]),
        ),
    );
  }
  for (const id of ["terminal", "date", "time"])
    by(id).addEventListener("change", draw);
  draw();
} catch {
  by("finding").textContent = "The timetable could not load.";
}
