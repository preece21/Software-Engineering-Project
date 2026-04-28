"""
ICS Calendar Parsing Module
----------------------------

This module is responsible ONLY for:

1) Downloading an ICS file from a URL
2) Parsing the ICS data using the `icalendar` library
3) Converting raw VEVENT components into normalized Event objects

It deliberately does NOT:
- Expand recurring events
- Filter events by time window
- Render UI
- Cache results

Design Philosophy:
External data (ICS format) should be converted immediately into a clean,
internal data model (Event class). After parsing, the rest of the app
should never need to understand ICS syntax.
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
import requests
import pytz
from icalendar import Calendar
from dateutil.rrule import rrulestr


# ---------------------------------------------------------------------------
# Event Model
# ---------------------------------------------------------------------------

@dataclass
class Event:
    """
    Internal representation of a calendar event.

    This class is intentionally decoupled from the `icalendar` library.
    Once an Event object is created, the rest of the application should
    not depend on ICS-specific structures.

    Attributes:
        uid:
            Unique identifier from the ICS file.
            Used to track updates or detect duplicate events.

        title:
            Event summary/title (maps from ICS "SUMMARY").

        start:
            Timezone-aware datetime when the event begins.

        end:
            Timezone-aware datetime when the event ends.
            May be None if not provided in the ICS file.

        location:
            Optional location string.

        description:
            Optional event description.

        rrule:
            Raw recurrence rule data (if present).
            This is NOT expanded here. Expansion should happen in a
            separate recurrence-processing layer.

        exdates:
            List of datetime instances that should be excluded from
            recurrence expansion.

        all_day:
            True if the event was defined as a date-only value in the ICS.
            Useful for rendering logic.
    """
    uid: str
    title: str
    start: datetime
    end: Optional[datetime]
    location: str = ""
    description: str = ""
    rrule: Optional[Dict[str, Any]] = None
    exdates: List[datetime] = field(default_factory=list)
    all_day: bool = False
    exclusive: bool = False

    def __str__(self) -> str:
        """
        Human-readable representation for debugging.
        """
        return (
            f"Event(title={self.title}, "
            f"start={self.start}, "
            f"end={self.end}, "
            f"all_day={self.all_day})"
        )


# ---------------------------------------------------------------------------
# ICS Fetching
# ---------------------------------------------------------------------------

def fetch_ics_from_url(url: str) -> bytes:
    """
    Downloads an ICS file from a publicly accessible URL.

    Parameters:
        url:
            The full URL to the published ICS calendar.

    Returns:
        Raw byte content of the ICS file.

    Why return bytes instead of string?
        The `icalendar` library expects raw byte input. Passing decoded
        strings can cause encoding issues for special characters.

    Raises:
        requests.HTTPError if the request fails (404, 403, etc.)
    """
    response = requests.get(url)
    response.raise_for_status()  # Fail early if network error occurs
    return response.content


# ---------------------------------------------------------------------------
# Datetime Normalization
# ---------------------------------------------------------------------------

def normalize_datetime(dt) -> (datetime, bool):
    """
    Converts ICS date or datetime values into a timezone-aware datetime.

    ICS values can be:
        - datetime with timezone
        - datetime without timezone
        - date (for all-day events)

    Returns:
        (normalized_datetime, all_day_flag)

    """
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            # If no timezone is provided, assume UTC
            dt = pytz.UTC.localize(dt)
        return dt, False

    elif isinstance(dt, date):
        # Date-only → All-day event
        dt_obj = datetime(dt.year, dt.month, dt.day, tzinfo=pytz.UTC)
        return dt_obj, True

    else:
        raise ValueError("Unsupported datetime format encountered in ICS")



# ---------------------------------------------------------------------------
# ICS Parsing
# ---------------------------------------------------------------------------

def parse_ics(ics_data: bytes) -> List[Event]:
    """
    Parses raw ICS byte data into a list of Event objects.

    Steps:
        1) Parse entire calendar structure using `icalendar`.
        2) Walk through components.
        3) Extract VEVENT components only.
        4) Normalize fields.
        5) Convert to internal Event objects.

    Parameters:
        ics_data:
            Raw ICS file contents (bytes).

    Returns:
        List[Event]

    """
    calendar = Calendar.from_ical(ics_data)
    events: List[Event] = []

    # Walk through all components in the ICS file
    for component in calendar.walk():

        # We only care about VEVENT components
        if component.name != "VEVENT":
            continue

        # Extract core properties with safe fallbacks
        uid = str(component.get("UID"))
        title = str(component.get("SUMMARY", ""))
        location = str(component.get("LOCATION", ""))
        description = str(component.get("DESCRIPTION", ""))

        # --- Start Time ---
        dtstart_raw = component.get("DTSTART").dt
        start, all_day = normalize_datetime(dtstart_raw)

        # --- End Time ---
        dtend_component = component.get("DTEND")
        if dtend_component:
            end, _ = normalize_datetime(dtend_component.dt)
        else:
            # Some events may omit DTEND
            end = None

        # --- Recurrence Rule (RRULE) ---
        rrule_component = component.get("RRULE")
        rrule = dict(rrule_component) if rrule_component else None

        # --- Exception Dates (EXDATE) ---
        exdates_list: List[datetime] = []
        exdate_component = component.get("EXDATE")

        if exdate_component:
            # EXDATE can appear multiple times or contain multiple values
            if not isinstance(exdate_component, list):
                exdate_component = [exdate_component]

            for ex in exdate_component:
                for dt in ex.dts:
                    ex_dt, _ = normalize_datetime(dt.dt)
                    exdates_list.append(ex_dt)

        # --- Room Reservation
        if title.startswith("Reserved"):
            exclusive = True
        else:
            exclusive = False
        
        # Create normalized internal Event object
        event = Event(
            uid=uid,
            title=title,
            start=start,
            end=end,
            location=location,
            description=description,
            rrule=rrule,
            exdates=exdates_list,
            all_day=all_day,
            exclusive = exclusive
        )

        events.append(event)

    return events


#---------------------------------------------
# Expand Events
#---------------------------------------------

def expand_event(event: Event, start_window: datetime, end_window: datetime) -> List[Event]:
    # ---------------------------
    # NON-RECURRING CASE
    # ---------------------------
    if event.rrule is None:
        if start_window <= event.start <= end_window:
            return [event]
        return []

    rrule = event.rrule or {}

    frequency = rrule.get("FREQ", [None])[0]
    if not frequency:
        return []

    frequency = frequency.upper()

    count = rrule.get("COUNT", [None])[0]
    until = rrule.get("UNTIL", [None])[0]

    # ---------------------------
    # DETERMINE STEP SIZE
    # ---------------------------
    if frequency == "DAILY":
        delta = timedelta(days=1)
    elif frequency == "WEEKLY":
        delta = timedelta(weeks=1)
    else:
        return []

    # ---------------------------
    # GENERATE ALL CANDIDATES
    # ---------------------------
    i = 0
    candidates = []

    while True:
        current_start = event.start + (delta * i)

        # UNTIL stops generation
        if until is not None and current_start > until:
            break

        # COUNT is based on recurrence index, not valid events
        if count is not None and i >= count:
            break

        candidates.append(
            Event(
                uid=event.uid,
                title=event.title,
                start=current_start,
                end=event.end + (delta * i) if event.end else None,
                location=event.location,
                description=event.description,
                rrule=event.rrule,
                exdates=event.exdates,
                all_day=event.all_day,
                exclusive=event.exclusive,
            )
        )

        i += 1

    # ---------------------------
    # APPLY EXDATE FILTER
    # ---------------------------
    filtered = [
        e for e in candidates
        if not any(e.start == ex for ex in event.exdates)
    ]

    # ---------------------------
    # APPLY WINDOW FILTER
    # ---------------------------
    return [
        e for e in filtered
        if start_window <= e.start < (end_window + timedelta(days=1))
        ]


def parse_from_calendar(url: str, start_window: datetime, end_window: datetime) -> List[Event]:
    bytes = fetch_ics_from_url(url)
    first_pass_events = parse_ics(bytes)

    second_pass_events = []

    for event in first_pass_events:
        recurring_event = expand_event(event, start_window, end_window)
        second_pass_events.append(recurring_event)
    
    return second_pass_events

def main():
    pass

if __name__ == "__main__":
    main()