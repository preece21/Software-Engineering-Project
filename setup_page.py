"""
Setup Page for Room Availability App
-------------------------------------

Displays a welcome screen on first launch where users can enter their ICS calendar link.
"""

import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from Parsing import fetch_ics_from_url, parse_ics
from config_manager import ConfigManager


class SetupPage(QWidget):
    """First-time setup page for entering ICS calendar link."""
    
    # Signal emitted when setup is complete
    setup_completed = pyqtSignal()
    
    def __init__(self):
        """Initialize the setup page."""
        super().__init__()
        self.config_manager = ConfigManager()
        self.init_ui()
    
    def init_ui(self):
        """Create the UI components."""
        self.setWindowTitle("Room Availability - Initial Setup")
        self.setGeometry(100, 100, 600, 300)
        
        main_layout = QVBoxLayout()
        
        # Title
        title = QLabel("Welcome to Room Availability Dashboard")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("To get started, please provide your calendar ICS link")
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)
        subtitle.setFont(subtitle_font)
        main_layout.addWidget(subtitle)
        
        # Instructions
        instructions = QLabel(
            "Enter the URL to your calendar's ICS file (e.g., from Google Calendar, "
            "Outlook, or any calendar application that supports .ics export).\n\n"
            "This file will be downloaded and cached locally for quick access."
        )
        instructions.setWordWrap(True)
        main_layout.addWidget(instructions)
        
        # Input section
        input_layout = QHBoxLayout()
        label = QLabel("Calendar ICS Link:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com/calendar.ics")
        input_layout.addWidget(label)
        input_layout.addWidget(self.url_input)
        main_layout.addLayout(input_layout)
        
        # Button section
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.test_button = QPushButton("Test Link")
        self.test_button.clicked.connect(self.test_link)
        button_layout.addWidget(self.test_button)
        
        self.save_button = QPushButton("Save & Continue")
        self.save_button.clicked.connect(self.save_setup)
        self.save_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 5px; }")
        button_layout.addWidget(self.save_button)
        
        main_layout.addLayout(button_layout)
        
        # Notes
        notes = QLabel(
            "Note: The calendar file will be automatically downloaded and saved in your "
            "local application directory. You can update this link later in the settings."
        )
        notes_font = QFont()
        notes_font.setPointSize(8)
        notes.setFont(notes_font)
        notes.setStyleSheet("color: gray;")
        notes.setWordWrap(True)
        main_layout.addWidget(notes)
        
        main_layout.addStretch()
        
        self.setLayout(main_layout)
    
    def test_link(self):
        """Test if the provided ICS link is valid."""
        url = self.url_input.text().strip()
        
        if not url:
            QMessageBox.warning(self, "Empty Link", "Please enter an ICS calendar link.")
            return
        
        try:
            # Try to fetch the ICS file
            ics_data = fetch_ics_from_url(url)
            
            # Try to parse it
            events = parse_ics(ics_data)
            
            QMessageBox.information(
                self, 
                "Success", 
                f"Calendar link is valid!\nFound {len(events)} events."
            )
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error", 
                f"Failed to load calendar:\n{str(e)}\n\n"
                "Please check the URL and try again."
            )
    
    def save_setup(self):
        """Save the ICS URL and download the calendar file."""
        url = self.url_input.text().strip()
        
        if not url:
            QMessageBox.warning(self, "Empty Link", "Please enter an ICS calendar link.")
            return
        
        try:
            # Fetch and save the ICS file
            ics_data = fetch_ics_from_url(url)
            self.config_manager.save_ics_file(ics_data)
            
            # Save the URL to config
            self.config_manager.set_ics_url(url)
            
            # Emit signal to indicate setup is complete
            self.setup_completed.emit()
            
        except Exception as e:
            print(f"Error in save_setup: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self, 
                "Error", 
                f"Failed to save calendar:\n{str(e)}"
            )
