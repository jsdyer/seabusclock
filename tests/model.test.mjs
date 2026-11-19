import test from "node:test";
import assert from "node:assert/strict";
import { profile, peak } from "../web/sea-model.mjs";

test("hourly peaks retain zero and skip missing readings", () => {
  const record = {
    entries: {
      "2025|Fall|MF": {
        Southbound: { 0: null, 8: 0, 16: 1052.1 },
        Northbound: { 17: 981.7 },
      },
    },
  };
  const day = profile(record, 2025, "Fall", "MF");
  assert.deepEqual(peak(day.Southbound), ["16", 1052.1]);
  assert.deepEqual(peak(day.Northbound), ["17", 981.7]);
  assert.deepEqual(peak({ 0: null, 6: 0 }), ["6", 0]);
  assert.equal(peak({ 0: null }), null);
  assert.deepEqual(profile(record, 2025, "Fall", "Sat"), {});
});

import { sailings } from "../web/model.mjs";
test("after-midnight sailing appears on the following civil date", () => {
  const data = {
    calendar: { "2026-10-01": ["late"], "2026-10-02": ["early"] },
    events: {
      late: [[1450, 1462, "Waterfront"]],
      early: [
        [410, 422, "Waterfront"],
        [415, 427, "Lonsdale Quay"],
      ],
    },
  };
  assert.deepEqual(sailings(data, "2026-10-02", "Waterfront", 0), [
    [10, 22],
    [410, 422],
  ]);
  assert.deepEqual(sailings(data, "2026-10-02", "Waterfront", 411), []);
});

test("a late-night search includes the next sailing and the following gap across midnight", () => {
  const data = {
    calendar: { "2026-11-18": ["night"], "2026-11-19": ["morning"] },
    events: {
      night: [
        [1426, 1438, "Waterfront"],
        [1456, 1468, "Waterfront"],
        [1486, 1498, "Waterfront"],
      ],
      morning: [[405, 417, "Waterfront"]],
    },
  };
  assert.deepEqual(sailings(data, "2026-11-18", "Waterfront", 1430), [
    [1456, 1468],
    [1486, 1498],
  ]);
});
