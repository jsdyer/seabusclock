import { serviceSets } from "./schedule.mjs";
export function sailings(data, day, terminal, from) {
  const times = serviceSets(data, day)
    .flatMap(({ group, offset }) =>
      group
        .filter((s) => s[2] === terminal)
        .map(([departure, arrival]) => [departure + offset, arrival + offset]),
    )
    .filter(([t]) => t >= from && t < 2880)
    .sort((a, b) => a[0] - b[0]);
  const overnight = times.findIndex(([departure]) => departure >= 1440);
  return overnight === -1 ? times : times.slice(0, overnight + 2);
}
