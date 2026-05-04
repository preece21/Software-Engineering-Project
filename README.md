# Software-Engineering-Project

## Room Availability Dashboard

A PyQt6-based desktop application for viewing room availability and events from an ICS calendar. The dashboard displays a 7-day view of upcoming events, shows real-time room status (busy/available/open), and automatically refreshes calendar data every 3 hours.

---

### First-Time Setup

When you launch the application for the first time, a setup page will appear prompting you to enter your calendar ICS link. This is a URL to a publicly accessible `.ics` (iCalendar) file.

**Where to find your ICS link:**
- **Google Calendar**: Calendar settings → Integrate calendar → Copy the "Public ICS URL"
- **Outlook/Microsoft**: Settings → Calendar → Shared Calendars → Publish a Calendar
- **Apple Calendar**: Export calendar → Copy the `.ics` file URL
- **Any calendar app**: Export settings typically have an option to generate an ICS URL

**What happens during setup:**

1. Enter your calendar ICS link in the setup page
2. Click "Test Link" to verify the URL is valid (optional but recommended)
3. Click "Save & Continue" to download and save the calendar
4. The calendar file is automatically cached in `~/.room_availability_app/ics_cache/`
5. The ICS link is saved in `~/.room_availability_app/config.json`

On subsequent launches, the app will use the saved configuration and cached calendar file.

---

### Installation

```bash
pip install -r requirements.txt
python room_availability_app.py
```

---

### Running Tests

```bash
pytest parser_test.py -v
```

No network connection or configuration is required to run the tests — they use self-contained data and test the ICS parsing and recurrence expansion logic in `Parsing.py`.

---

### Configuration

- **Config location**: `~/.room_availability_app/config.json`
- **Cache location**: `~/.room_availability_app/ics_cache/calendar.ics`

To reset the app and enter a new calendar link, click the "Remove Calendar" button in the dashboard. The app will clear the config and cache, and will prompt for a new ICS link on next launch.

---

### Project Structure

| File | Description |
|------|-------------|
| `room_availability_app.py` | Main application window, calendar rendering, and status indicator |
| `setup_page.py` | First-time setup UI for entering the ICS calendar link |
| `Parsing.py` | ICS fetching, parsing, and recurring event expansion |
| `config_manager.py` | Persists the ICS URL and cached calendar file to disk |
| `parser_test.py` | Pytest test suite for the parsing and recurrence logic |
| `requirements.txt` | Python package dependencies |

---

### Dependencies

- **PyQt6**: GUI framework
- **requests**: HTTP requests for downloading calendar files
- **icalendar**: ICS file parsing
- **pytz**: Timezone handling
- **python-dateutil**: Recurring event expansion (RRULE support)
- **pytest**: Test runner