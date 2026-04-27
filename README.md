# Software-Engineering-Project

## Room Availability Dashboard

A PyQt6-based application for viewing room availability and events from an ICS calendar.

### First-Time Setup

When you launch the application for the first time, a setup page will appear prompting you to enter your calendar ICS link. This is a URL to a publicly accessible `.ics` (iCalendar) file.

**Where to find your ICS link:**
- **Google Calendar**: Calendar settings → Integrate calendar → Copy the "Public ICS URL"
- **Outlook/Microsoft**: Calendar sharing → Get sharing link (export as ICS)
- **Apple Calendar**: Export calendar → Copy the `.ics` file URL
- **Any calendar app**: Export settings typically have an option to generate an ICS URL

### What happens during setup:

1. Enter your calendar ICS link in the setup page
2. Click "Test Link" to verify the URL is valid (optional but recommended)
3. Click "Save & Continue" to download and save the calendar
4. The calendar file is automatically cached in `~/.room_availability_app/ics_cache/`
5. The ICS link is saved in `~/.room_availability_app/config.json`

### Configuration

- **Config Location**: `~/.room_availability_app/config.json`
- **Cache Location**: `~/.room_availability_app/ics_cache/calendar.ics`

On subsequent launches, the app will use the saved configuration and cached calendar file.

### Installation

```bash
pip install -r requirements.txt
python room_availability_app.py
```

### Dependencies

- PyQt6: GUI framework
- requests: HTTP requests for downloading calendar files
- icalendar: ICS file parsing
- pytz: Timezone handling