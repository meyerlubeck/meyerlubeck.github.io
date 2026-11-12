import datetime
import unittest

import db


def ms(day, hour=12):
    return int(datetime.datetime.fromisoformat(f"{day}T{hour:02d}:00:00").timestamp() * 1000)


class SnapshotTest(unittest.TestCase):
    def setUp(self):
        self.con = db.connect(":memory:")
        db.add_award(self.con, [
            ("ICN-JFK", "20270501", "P", 1, 1, ms("2026-11-01")),
            ("ICN-JFK", "20270501", "E", 1, 1, ms("2026-11-01")),
            ("ICN-JFK", "20270501", "P", 0, 1, ms("2026-11-03")),  # 나중에 닫힘
        ])
        db.add_revenue(self.con, [
            ("ICN-JFK", "20261201", "KE081", {"J": 9, "C": 2}, ms("2026-11-01")),
            ("ICN-JFK", "20261201", "KE081", {"J": 1}, ms("2026-11-03")),
            ("ICN-JFK", "20261201", "KE085", {"J": 0, "C": 4}, ms("2026-11-03")),
        ])

    def test_latest_observation_wins(self):
        s = db.snapshot(self.con)
        cell = s["current"]["ICN-JFK"]["20270501"]
        self.assertEqual((cell["E"], cell["P"], cell["F"], cell["peak"]), (True, False, False, True))
        self.assertEqual(cell["ts"], ms("2026-11-03"))
        self.assertEqual(s["days"], ["2026-11-01", "2026-11-03"])

    def test_asof_rewinds(self):
        s = db.snapshot(self.con, "2026-11-02")
        self.assertTrue(s["current"]["ICN-JFK"]["20270501"]["P"])
        self.assertEqual(s["revenue"]["ICN-JFK"]["20261201"]["classes"], {"J": 9, "C": 2})

    def test_revenue_merges_flights_of_latest_run_only(self):
        rv = db.snapshot(self.con)["revenue"]["ICN-JFK"]["20261201"]
        self.assertEqual(rv["classes"], {"J": 1, "C": 4})
        self.assertEqual(rv["max"], 4)


if __name__ == "__main__":
    unittest.main()
