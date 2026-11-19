export function profile(dataset, year, season, day) {
  return dataset.entries[[year, season, day].join("|")] || {};
}
export function peak(points) {
  const entries = Object.entries(points || {}).filter(([, v]) =>
    Number.isFinite(v),
  );
  entries.sort((a, b) => b[1] - a[1] || Number(a[0]) - Number(b[0]));
  return entries[0] || null;
}
