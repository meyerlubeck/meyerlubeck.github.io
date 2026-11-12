"""SQLite 저장소: 관측을 그대로 쌓고(append-only), 화면용 스냅샷을 만들어 준다."""
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("data.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS award(
  route TEXT, date TEXT, cabin TEXT,   -- 'ICN-JFK', 'YYYYMMDD', 'E'|'P'|'F'
  avail INTEGER, peak INTEGER, ts INTEGER);  -- ts = 관측 시각(ms)
CREATE INDEX IF NOT EXISTS award_key ON award(route, date, cabin, ts);
CREATE TABLE IF NOT EXISTS revenue(
  route TEXT, date TEXT, flight TEXT,
  classes TEXT, ts INTEGER);           -- classes = JSON {"J": 9, "C": 4}
CREATE INDEX IF NOT EXISTS revenue_key ON revenue(route, date, ts);
"""

DAY = "date(ts/1000, 'unixepoch', 'localtime')"


def connect(path=DB_PATH):
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    return con


def add_award(con, rows):
    """rows: (route, date, cabin, avail, peak, ts)"""
    con.executemany("INSERT INTO award VALUES (?,?,?,?,?,?)", rows)
    con.commit()


def add_revenue(con, rows):
    """rows: (route, date, flight, classes_dict, ts). 한 번의 조회에서 나온 편들은 같은 ts를 쓴다."""
    con.executemany(
        "INSERT INTO revenue VALUES (?,?,?,?,?)",
        [(r, d, f, json.dumps(c), ts) for r, d, f, c, ts in rows],
    )
    con.commit()


def snapshot(con, asof=None):
    """asof('YYYY-MM-DD')까지의 관측 중 날짜별 마지막 상태. None이면 현재."""
    asof = asof or "9999-12-31"
    current, revenue = {}, {}
    # SQLite: MAX(ts)와 함께 고른 나머지 컬럼은 그 최댓값 행의 값이다.
    for route, date, cabin, avail, peak, ts in con.execute(
        f"SELECT route, date, cabin, avail, peak, MAX(ts) FROM award "
        f"WHERE {DAY} <= ? GROUP BY route, date, cabin", (asof,)
    ):
        cell = current.setdefault(route, {}).setdefault(
            date, {"E": False, "P": False, "F": False, "peak": False, "ts": 0})
        cell[cabin] = bool(avail)
        cell["peak"] = cell["peak"] or bool(peak)
        cell["ts"] = max(cell["ts"], ts)
    # 유상: 그 날짜의 가장 최근 조회에 나온 편들을 클래스별 최댓값으로 합친다.
    for route, date, classes, ts in con.execute(
        f"SELECT r.route, r.date, r.classes, r.ts FROM revenue r JOIN ("
        f"  SELECT route, date, MAX(ts) m FROM revenue WHERE {DAY} <= ? GROUP BY route, date"
        f") x ON r.route = x.route AND r.date = x.date AND r.ts = x.m", (asof,)
    ):
        cell = revenue.setdefault(route, {}).setdefault(date, {"classes": {}, "max": 0, "ts": ts})
        for k, v in json.loads(classes).items():
            cell["classes"][k] = max(cell["classes"].get(k, 0), v)
        cell["max"] = max(cell["classes"].values(), default=0)
    days = [d for (d,) in con.execute(f"SELECT DISTINCT {DAY} FROM award ORDER BY 1")]
    return {"current": current, "revenue": revenue, "days": days}
