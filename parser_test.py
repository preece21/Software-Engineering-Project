import pytest
from datetime import datetime, timedelta
import pytz

from Parsing import Event, expand_event

UTC = pytz.UTC

#--------------------------------
# Event Maker to reduce Boilerplate
#--------------------------------
def make_event(
    start,
    end=None,
    rrule=None,
    exdates=None,
    all_day=False,
):
    return Event(
        uid="test-uid",
        title="Test Event",
        start=start,
        end=end,
        rrule=rrule,
        exdates=exdates or [],
        all_day=all_day,
    )

#------------------------------------------
# Test Cases
#------------------------------------------

def test_non_recurring_event_returns_itself():
    start = datetime(2026, 1, 1, 10, tzinfo=UTC)
    end = start + timedelta(hours=1)

    event = make_event(start, end)

    results = expand_event(
        event,
        start_window=datetime(2026, 1, 1, tzinfo=UTC),
        end_window=datetime(2026, 1, 2, tzinfo=UTC),
    )

    assert len(results) == 1
    assert results[0].start == start
    assert results[0].end == end


def test_non_recurring_event_outside_window():
    start = datetime(2026, 1, 5, 10, tzinfo=UTC)

    event = make_event(start)

    results = expand_event(
        event,
        start_window=datetime(2026, 1, 1, tzinfo=UTC),
        end_window=datetime(2026, 1, 2, tzinfo=UTC),
    )

    assert results == []


def test_daily_recurrence_basic():
    start = datetime(2026, 1, 1, 10, tzinfo=UTC)
    end = start + timedelta(hours=1)

    event = make_event(
        start,
        end,
        rrule={"FREQ": ["DAILY"], "COUNT": [3]},
    )

    results = expand_event(
        event,
        start_window=datetime(2026, 1, 1, tzinfo=UTC),
        end_window=datetime(2026, 1, 10, tzinfo=UTC),
    )

    assert len(results) == 3
    assert results[0].start == datetime(2026, 1, 1, 10, tzinfo=UTC)
    assert results[1].start == datetime(2026, 1, 2, 10, tzinfo=UTC)
    assert results[2].start == datetime(2026, 1, 3, 10, tzinfo=UTC)

def test_recurrence_clipped_to_window():
    start = datetime(2026, 1, 1, 10, tzinfo=UTC)

    event = make_event(
        start,
        start + timedelta(hours=1),
        rrule={"FREQ": ["DAILY"], "COUNT": [10]},
    )

    results = expand_event(
        event,
        start_window=datetime(2026, 1, 3, tzinfo=UTC),
        end_window=datetime(2026, 1, 5, tzinfo=UTC),
    )

    assert len(results) == 3
    assert results[0].start.day == 3
    assert results[-1].start.day == 5

def test_exdate_removes_occurrence():
    start = datetime(2026, 1, 1, 10, tzinfo=UTC)

    exdate = datetime(2026, 1, 3, 10, tzinfo=UTC)

    event = make_event(
        start,
        start + timedelta(hours=1),
        rrule={"FREQ": ["DAILY"], "COUNT": [5]},
        exdates=[exdate],
    )

    results = expand_event(
        event,
        start_window=datetime(2026, 1, 1, tzinfo=UTC),
        end_window=datetime(2026, 1, 10, tzinfo=UTC),
    )

    starts = [e.start for e in results]

    assert len(results) == 4
    assert exdate not in starts

def test_weekly_recurrence():
    start = datetime(2026, 1, 5, 10, tzinfo=UTC)  # Monday

    event = make_event(
        start,
        start + timedelta(hours=1),
        rrule={"FREQ": ["WEEKLY"], "COUNT": [2]},
    )

    results = expand_event(
        event,
        start_window=datetime(2026, 1, 1, tzinfo=UTC),
        end_window=datetime(2026, 2, 1, tzinfo=UTC),
    )

    assert len(results) == 2
    assert results[1].start == start + timedelta(days=7)

def test_rrule_until():
    start = datetime(2026, 1, 1, 10, tzinfo=UTC)

    event = make_event(
        start,
        start + timedelta(hours=1),
        rrule={
            "FREQ": ["DAILY"],
            "UNTIL": [datetime(2026, 1, 3, 10, tzinfo=UTC)],
        },
    )

    results = expand_event(
        event,
        start_window=datetime(2026, 1, 1, tzinfo=UTC),
        end_window=datetime(2026, 1, 10, tzinfo=UTC),
    )

    assert len(results) == 3  # Jan 1, 2, 3

def test_duration_preserved():
    start = datetime(2026, 1, 1, 10, tzinfo=UTC)
    end = start + timedelta(hours=2)

    event = make_event(
        start,
        end,
        rrule={"FREQ": ["DAILY"], "COUNT": [3]},
    )

    results = expand_event(
        event,
        start_window=datetime(2026, 1, 1, tzinfo=UTC),
        end_window=datetime(2026, 1, 10, tzinfo=UTC),
    )

    for e in results:
        assert (e.end - e.start) == timedelta(hours=2)

def test_all_day_event_recurrence():
    start = datetime(2026, 1, 1, tzinfo=UTC)

    event = make_event(
        start,
        None,
        rrule={"FREQ": ["DAILY"], "COUNT": [2]},
        all_day=True,
    )

    results = expand_event(
        event,
        start_window=datetime(2026, 1, 1, tzinfo=UTC),
        end_window=datetime(2026, 1, 5, tzinfo=UTC),
    )

    assert len(results) == 2
    assert all(e.all_day for e in results)
    
def test_event_with_no_end():
      start = datetime(2026, 1, 1, 10, tzinfo=UTC)

      event = make_event(
        start,
        None,
        rrule={"FREQ": ["DAILY"], "COUNT": [2]},
      )

      results = expand_event(
        event,
        start_window=datetime(2026, 1, 1, tzinfo=UTC),
        end_window=datetime(2026, 1, 5, tzinfo=UTC),
      )

      assert all(e.end is None for e in results)

def test_uid_preserved():
      start = datetime(2026, 1, 1, 10, tzinfo=UTC)

      event = make_event(
          start,
          start + timedelta(hours=1),
          rrule={"FREQ": ["DAILY"], "COUNT": [3]},
      )

      results = expand_event(
        event,
        start_window=datetime(2026, 1, 1, tzinfo=UTC),
        end_window=datetime(2026, 1, 10, tzinfo=UTC),
      )

      assert all(e.uid == "test-uid" for e in results)
      
def main():
    pass


if __name__ == "__main__":
    main()