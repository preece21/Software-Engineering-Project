import sys
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import QTimer, QDateTime
from PyQt6.QtGui import QPalette, QColor
import random  # For simulating events

class RoomAvailabilityApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Room Availability Dashboard")
        self.setGeometry(100, 100, 1400, 400)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout(central_widget)

        # Day zones layout
        days_layout = QHBoxLayout()
        main_layout.addLayout(days_layout)

        # Get the Sunday of the current week
        today = datetime.now()
        days_until_sunday = (today.weekday() + 1) % 7  # Sunday is 0, Monday is 1, etc.
        sunday = today - timedelta(days=days_until_sunday)

        # Create zones for each day of the week (Sunday to Saturday)
        self.day_zones = []
        day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        
        for i in range(7):
            current_date = sunday + timedelta(days=i)
            day_label = f"{day_names[i]}\n{current_date.strftime('%m/%d')}"
            
            zone = QFrame()
            zone.setFrameStyle(QFrame.Shape.Box)
            zone.setLineWidth(2)
            zone_layout = QVBoxLayout(zone)
            zone_layout.addWidget(QLabel(f"<b>{day_label}</b>"))
            # Simulate events for each day
            events_label = QLabel("Events: " + self.simulate_events())
            zone_layout.addWidget(events_label)
            days_layout.addWidget(zone)
            self.day_zones.append(zone)

        # Status section
        self.status_label = QLabel("Status: Checking...")
        self.status_label.setFixedHeight(200)
        self.status_label.setAutoFillBackground(True)
        main_layout.addWidget(self.status_label)

        # Timer to update status every 5 seconds (simulate real-time)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(5000)  # 5 seconds

        # Initial update
        self.update_status()

    def simulate_events(self):
        # Simulate some events for demonstration
        events = ["Meeting 10-11 AM", "Lunch 12-1 PM", "Workshop 2-4 PM"]
        return ", ".join(random.sample(events, random.randint(0, 3)))

    def update_status(self):
        # Simulate checking current calendar state
        # In a real app, this would query a calendar API or local data
        current_time = QDateTime.currentDateTime()
        hour = current_time.time().hour()

        # Simple logic: Green if no events in current hour, Yellow if minor event, Red if busy
        if hour < 9 or hour > 17:  # Outside work hours
            color = QColor("green")
            text = "Room Open (No Events)"
        elif hour in [10, 14]:  # Simulate busy times
            color = QColor("red")
            text = "Room Busy (Event in Progress)"
        else:
            color = QColor("yellow")
            text = "Room Available (Event Soon)"

        palette = self.status_label.palette()
        palette.setColor(QPalette.ColorRole.Window, color)
        self.status_label.setPalette(palette)
        self.status_label.setText(f"Status: {text}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RoomAvailabilityApp()
    window.show()
    sys.exit(app.exec())