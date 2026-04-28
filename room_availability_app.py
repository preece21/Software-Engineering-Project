import sys
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QMessageBox, QSizePolicy, QScrollArea
from PyQt6.QtCore import QTimer, QDateTime, Qt
from PyQt6.QtGui import QPalette, QColor
import random  # For simulating events
import pytz  # For timezone handling
from dateutil.rrule import rrulestr, rruleset

from config_manager import ConfigManager
from setup_page import SetupPage
from Parsing import parse_ics, Event, fetch_ics_from_url, parse_from_calendar

class RoomAvailabilityApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Room Availability Dashboard")
        self.setGeometry(100, 100, 1400, 600)  # Increased height for better event display

        # Load calendar data
        self.config_manager = ConfigManager()
        self.week_start = self.get_current_day_start()
        self.week_end = self.week_start + timedelta(days=7)
        self.events = self.parse_calendar_events()

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(4, 2, 4, 6)
        main_layout.setSpacing(2)

        # Top row: week label only
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(2)
        self.week_label = QLabel(f"Showing 7 days starting {self.week_start.date()}")
        self.week_label.setStyleSheet("font-weight: bold; font-size: 12px; margin-bottom: 0px;")
        top_layout.addWidget(self.week_label)
        top_layout.addStretch()
        main_layout.addLayout(top_layout)

        # Day zones layout with horizontal scrolling so all 7 days can be seen
        days_layout = QHBoxLayout()
        days_layout.setSpacing(4)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setMinimumHeight(420)

        scroll_container = QWidget()
        scroll_container.setLayout(days_layout)
        scroll_area.setWidget(scroll_container)

        main_layout.addWidget(scroll_area, 1)

        # Status section
        self.status_label = QLabel("Status: Checking...")
        self.status_label.setMinimumHeight(200)
        self.status_label.setMaximumHeight(300)
        self.status_label.setStyleSheet("padding: 2px; font-size: 12px;")
        self.status_label.setAutoFillBackground(True)
        main_layout.addWidget(self.status_label)

        # Get the start of the current display period (today)
        today = self.week_start

        # Create zones for each day (today + next 6 days)
        self.day_zones = []
        
        for i in range(7):
            current_date = today + timedelta(days=i)
            day_name = current_date.strftime('%A')  # Full day name (Monday, Tuesday, etc.)
            day_label = f"{day_name}\n{current_date.strftime('%m/%d')}"
            
            zone = QFrame()
            zone.setFrameStyle(QFrame.Shape.Box)
            zone.setLineWidth(2)
            zone.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            zone_layout = QVBoxLayout(zone)
            zone_layout.setContentsMargins(6, 6, 6, 6)
            zone_layout.setSpacing(4)
            zone_layout.addWidget(QLabel(f"<b>{day_label}</b>"))
            
            # Get real events for each day
            day_events = self.get_events_for_day(current_date)
            if day_events:
                for event_text in day_events:
                    event_label = QLabel(f"{event_text}")
                    event_label.setWordWrap(True)
                    event_label.setStyleSheet(
                        "background-color: #0078d4;"
                        "color: white;"
                        "border: 1px solid #005a9e;"
                        "border-radius: 10px;"
                        "padding: 6px 8px;"
                        "margin-bottom: 4px;"
                    )
                    zone_layout.addWidget(event_label)
            else:
                no_events_label = QLabel("No events")
                no_events_label.setStyleSheet("color: gray; font-style: italic;")
                zone_layout.addWidget(no_events_label)
            
            days_layout.addWidget(zone)
            self.day_zones.append(zone)

        # Control buttons section
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(4)
        button_layout.addStretch()
        
        remove_button = QPushButton("Remove Calendar")
        remove_button.setStyleSheet("background-color: #f44336; color: white; padding: 5px;")
        remove_button.clicked.connect(self.remove_calendar_link)
        button_layout.addWidget(remove_button)
        
        main_layout.addLayout(button_layout)

        # Timer to update status every 5 seconds (simulate real-time)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(5000)  # 5 seconds

        # Timer to check for day changes and refresh display daily
        self.day_check_timer = QTimer()
        self.day_check_timer.timeout.connect(self.check_day_change)
        self.day_check_timer.start(60 * 60 * 1000)  # Check every hour

        # Timer to refresh calendar data every 3 hours
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_calendar_data)
        self.refresh_timer.start(3 * 60 * 60 * 1000)  # 3 hours in milliseconds

        # Initial update
        self.update_status()

    def parse_calendar_events(self):
        """Parse the calendar from URL and return expanded Event objects."""
        try:
            ics_url = self.config_manager.get_ics_url()
            if ics_url:
                ics_data = fetch_ics_from_url(ics_url)
                raw_events = parse_ics(ics_data)
                # Use expand_recurring_events (dateutil-backed) so that BYDAY rules
                # like MO,WE,FR are correctly expanded — the custom expand_event in
                # Parsing.py only handles simple DAILY/WEEKLY and ignores BYDAY.
                expanded = self.expand_recurring_events(raw_events, self.week_start, self.week_end)
                return sorted(expanded, key=lambda e: e.start)
            return []
        except Exception as e:
            print(f"Error parsing calendar: {e}")
            return []

    def get_local_timezone(self):
        """Return the local timezone for the current system."""
        return datetime.now().astimezone().tzinfo

    def get_current_week_start(self):
        """Return the start of the current week (Sunday) at local midnight."""
        now = datetime.now().astimezone(self.get_local_timezone())
        days_until_sunday = (now.weekday() + 1) % 7
        week_start = now - timedelta(days=days_until_sunday)
        return week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    def get_current_day_start(self):
        """Return the start of the current day (today) at local midnight."""
        now = datetime.now().astimezone(self.get_local_timezone())
        return now.replace(hour=0, minute=0, second=0, microsecond=0)

    def get_week_start(self, dt):
        """Return the Sunday start of the given date/time in local timezone."""
        local_tz = self.get_local_timezone()
        dt_local = dt.astimezone(local_tz)
        days_until_sunday = (dt_local.weekday() + 1) % 7
        week_start = dt_local - timedelta(days=days_until_sunday)
        return week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    def event_in_range(self, event, start, end):
        """Check whether an event falls within a given period."""
        event_start = event.start
        event_end = event.end if event.end else event.start + timedelta(hours=1)
        return event_end >= start and event_start < end

    def rrule_to_string(self, rrule_dict):
        """Convert an RRULE dictionary into a string compatible with dateutil."""
        if isinstance(rrule_dict, str):
            return rrule_dict
        parts = []
        for key, value in rrule_dict.items():
            if isinstance(value, list):
                parts.append(f"{key}={','.join(str(v) for v in value)}")
            else:
                parts.append(f"{key}={value}")
        return ";".join(parts)

    def expand_recurring_events(self, events, period_start, period_end):
        """Expand recurring events into individual occurrences for the week."""
        expanded_events = []
        duration_cache = {}

        for event in events:
            if event.rrule:
                try:
                    rule_string = self.rrule_to_string(event.rrule)
                    rules = rruleset()
                    rules.rrule(rrulestr(rule_string, dtstart=event.start))

                    for ex in event.exdates:
                        rules.exdate(ex)

                    duration = (event.end - event.start) if event.end else timedelta(hours=1)
                    duration_cache[event.uid] = duration

                    for occurrence in rules.between(period_start, period_end, inc=True):
                        expanded_events.append(Event(
                            uid=f"{event.uid}-{occurrence.isoformat()}",
                            title=event.title,
                            start=occurrence,
                            end=occurrence + duration,
                            location=event.location,
                            description=event.description,
                            rrule=None,
                            exdates=[],
                            all_day=event.all_day
                        ))
                except Exception as e:
                    print(f"Failed to expand recurring event {event.uid}: {e}")
                    # Fallback: include the event only if it intersects the requested week
                    event_start = event.start
                    event_end = event.end if event.end else event.start + timedelta(hours=1)
                    if event_end >= period_start and event_start < period_end:
                        expanded_events.append(event)
            else:
                # Only keep events that are within the current week range
                event_start = event.start
                event_end = event.end if event.end else event.start + timedelta(hours=1)
                if event_end >= period_start and event_start < period_end:
                    expanded_events.append(event)

        return sorted(expanded_events, key=lambda e: e.start)

    def get_events_for_day(self, date):
        """Get events for a specific date."""
        day_events = []
        local_tz = datetime.now().astimezone().tzinfo
        target_date = date.date()

        for event in self.events:
            if event.all_day:
                event_date = event.start.date()
            else:
                event_date = event.start.astimezone(local_tz).date()

            if event_date == target_date:
                day_events.append(event)

        day_events.sort(key=lambda e: e.start)

        formatted_events = []
        for event in day_events:
            if event.all_day:
                formatted_events.append(f"{event.title} (All Day)")
            else:
                start_time = event.start.astimezone(local_tz).strftime("%I:%M %p")
                end_time = (event.end.astimezone(local_tz).strftime("%I:%M %p")
                            if event.end else "")
                if end_time:
                    formatted_events.append(f"{start_time} - {end_time}: {event.title}")
                else:
                    formatted_events.append(f"{start_time}: {event.title}")

        return formatted_events

    def simulate_events(self):
        # Simulate some events for demonstration
        events = ["Meeting 10-11 AM", "Lunch 12-1 PM", "Workshop 2-4 PM"]
        return ", ".join(random.sample(events, random.randint(0, 3)))

    def update_status(self):
        # Check current calendar state for real events
        current_time = datetime.now(pytz.UTC)  # Make timezone-aware
        
        # Check if there's an event happening right now
        current_event = None
        next_event = None
        
        for event in self.events:
            # Handle events without end time (assume 1 hour duration)
            event_end = event.end if event.end else event.start + timedelta(hours=1)
            
            if event.start <= current_time < event_end:
                current_event = event
                break
            elif event.start > current_time:
                if next_event is None or event.start < next_event.start:
                    next_event = event
        
        if current_event:
            color = QColor("red")
            text = f"Room Busy - {current_event.title}"
        elif next_event and (next_event.start - current_time).total_seconds() < 3600:  # Next event within 1 hour
            color = QColor("yellow")
            time_until = int((next_event.start - current_time).total_seconds() / 60)
            text = f"Room Available - Next event in {time_until} minutes"
        else:
            color = QColor("green")
            text = "Room Open (No Events)"

        palette = self.status_label.palette()
        palette.setColor(QPalette.ColorRole.Window, color)
        self.status_label.setPalette(palette)
        self.status_label.setText(f"Status: {text}")

    def refresh_calendar_data(self):
        """Refresh calendar data by downloading from URL and updating the display."""
        try:
            # Get the ICS URL
            ics_url = self.config_manager.get_ics_url()
            if not ics_url:
                print("No ICS URL configured, skipping refresh")
                return

            # Fetch new ICS data
            print("Refreshing calendar data...")
            ics_data = fetch_ics_from_url(ics_url)
            
            # Save to cache
            self.config_manager.save_ics_file(ics_data)
            
            # Re-parse events
            ics_data = fetch_ics_from_url(ics_url)
            raw_events = parse_ics(ics_data)
            self.events = self.expand_recurring_events(raw_events, self.week_start, self.week_end)
            self.events = sorted(self.events, key=lambda e: e.start)
            
            # Update the display
            self.update_calendar_display()
            
            print("Calendar data refreshed successfully")
            
        except Exception as e:
            print(f"Error refreshing calendar data: {e}")
            # Could show a message to the user, but for now just log it

    def check_day_change(self):
        """Check if the day has changed and update the display if needed."""
        current_day_start = self.get_current_day_start()
        if current_day_start != self.week_start:
            print("Day has changed, updating display...")
            # Update the week boundaries
            self.week_start = current_day_start
            self.week_end = self.week_start + timedelta(days=7)
            
            # Re-parse events for the new period
            self.events = self.parse_calendar_events()
            
            # Update the display
            self.update_calendar_display()
            
            # Update the week label
            self.week_label.setText(f"Showing 7 days starting {self.week_start.date()}")

    def update_calendar_display(self):
        """Update the calendar display with current events."""
        # Clear existing day zones
        for zone in self.day_zones:
            zone.setParent(None)
            zone.deleteLater()
        
        self.day_zones = []
        
        # Get the start of the current display period (today)
        today = self.week_start
        
        # Get the days_layout from the scroll area
        main_layout = self.centralWidget().layout()
        scroll_area = main_layout.itemAt(1).widget()
        days_layout = scroll_area.widget().layout()
        
        for i in range(7):
            current_date = today + timedelta(days=i)
            day_name = current_date.strftime('%A')  # Full day name (Monday, Tuesday, etc.)
            day_label = f"{day_name}\n{current_date.strftime('%m/%d')}"
            
            zone = QFrame()
            zone.setFrameStyle(QFrame.Shape.Box)
            zone.setLineWidth(2)
            zone.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            zone_layout = QVBoxLayout(zone)
            zone_layout.setContentsMargins(6, 6, 6, 6)
            zone_layout.setSpacing(4)
            zone_layout.addWidget(QLabel(f"<b>{day_label}</b>"))
            
            # Get real events for each day
            day_events = self.get_events_for_day(current_date)
            if day_events:
                for event_text in day_events:
                    event_label = QLabel(f"{event_text}")
                    event_label.setWordWrap(True)
                    event_label.setStyleSheet(
                        "background-color: #0078d4;"
                        "color: white;"
                        "border: 1px solid #005a9e;"
                        "border-radius: 10px;"
                        "padding: 6px 8px;"
                        "margin-bottom: 4px;"
                    )
                    zone_layout.addWidget(event_label)
            else:
                no_events_label = QLabel("No events")
                no_events_label.setStyleSheet("color: gray; font-style: italic;")
                zone_layout.addWidget(no_events_label)
            
            days_layout.addWidget(zone)
            self.day_zones.append(zone)
    
    def remove_calendar_link(self):
        """Remove the calendar link and cached data."""
        reply = QMessageBox.question(
            self,
            "Remove Calendar Link",
            "Are you sure you want to remove the calendar link and cached data? "
            "The application will restart to allow you to add a new calendar.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clear the configuration
            self.config_manager.clear_ics_data()
            QMessageBox.information(
                self,
                "Calendar Removed",
                "Calendar link and data have been removed. The application will now close. "
                "Please restart to add a new calendar."
            )
            # Close the application
            sys.exit(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Check if setup is needed
    config_manager = ConfigManager()
    
    # Keep references to prevent garbage collection
    main_window = None
    setup_page = None
    
    def create_and_show_main_window():
        """Create and display the main application window."""
        global main_window
        try:
            main_window = RoomAvailabilityApp()
            main_window.show()
        except Exception as e:
            print(f"Error creating/showing main window: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(None, "Error", f"Failed to create main window:\n{e}")
            sys.exit(1)
    
    if not config_manager.has_ics_configured():
        # Show setup page for first-time users
        setup_page = SetupPage()
        
        def on_setup_complete():
            if setup_page:
                setup_page.close()
            create_and_show_main_window()
        
        setup_page.setup_completed.connect(on_setup_complete)
        setup_page.show()
    else:
        # Show main window for returning users
        create_and_show_main_window()
    
    sys.exit(app.exec())