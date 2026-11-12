# ke-seats

대한항공 마일리지(보너스) 좌석과 유상 비즈니스 잔여석을 맥북에서 수집해 달력으로 보는 도구.

## 상태

- [x] `db.py` — 관측을 SQLite(`data.db`)에 쌓고 날짜별 최신 상태/과거 시점 스냅샷을 만든다
- [x] `server.py`, `index.html` — 로컬 달력 화면 (노선·방향 선택, 시점 되감기)
- [ ] 수집기 — 대한항공 조회 요청 형식(브라우저 HAR)을 확인한 뒤 작성

수집기가 없으므로 지금은 화면에 "수집된 데이터 없음"이 나온다.

## 실행

파이썬 3 표준 라이브러리만 쓴다.

```
python3 server.py        # http://127.0.0.1:8765
python3 -m unittest      # 테스트
```

## 수집기가 넣을 데이터

```python
import db
con = db.connect()
db.add_award(con, [("ICN-JFK", "20270501", "P", 1, 0, ts_ms)])            # cabin: E/P/F, avail, peak
db.add_revenue(con, [("ICN-JFK", "20261201", "KE081", {"J": 9}, ts_ms)])  # 예약클래스별 잔여석
```
