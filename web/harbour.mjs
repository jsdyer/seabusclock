import { by, node, row, options, read, comma } from "./ui.mjs";
import { profile, peak } from "./sea-model.mjs";
const hour = (h) => String(h).padStart(2, "0") + ":00";
try {
  const data = await read("seabus");
  options(
    by("syear"),
    data.years
      .slice()
      .reverse()
      .map((v) => [v, v]),
  );
  by("sea-edition").textContent =
    "Performance review " +
    data.edition +
    " · retrieved " +
    data.retrieved +
    " · Pacific time";
  function draw() {
    const dirs = ["Southbound", "Northbound"],
      stats = profile(
        data,
        by("syear").value,
        by("sseason").value,
        by("sday").value,
      );
    const findings = dirs.map((dir) => {
      const best = peak(stats[dir]);
      return best
        ? dir +
            " peaks at " +
            hour(best[0]) +
            " with " +
            comma(best[1]) +
            " average passengers."
        : dir + " has no reported volume.";
    });
    by("speak").textContent = findings.join(" ");
    by("srows").replaceChildren();
    by("splot").replaceChildren();
    const high = Math.max(
      1,
      ...Object.values(stats)
        .flatMap((x) => Object.values(x))
        .filter(Number.isFinite),
    );
    for (let h = 0; h < 24; h++) {
      const values = dirs.map((d) => stats[d]?.[h]);
      by("srows").append(row([hour(h), ...values.map(comma)]));
      if (values.every((v) => v == null)) continue;
      const item = node("div", null, "spark"),
        tracks = node("div", null, "tracks");
      item.append(node("span", hour(h)), tracks);
      values.forEach((v, i) => {
        const line = node("div", null, "trackline"),
          bar = node("span", null, "strip " + (i ? "second" : ""));
        bar.style.width = (v == null ? 0 : (76 * v) / high) + "%";
        line.append(bar, node("span", comma(v)));
        tracks.append(line);
      });
      by("splot").append(item);
    }
  }
  for (const id of ["syear", "sseason", "sday"])
    by(id).addEventListener("change", draw);
  draw();
} catch {
  by("speak").textContent = "Seasonal passenger figures could not load.";
}
