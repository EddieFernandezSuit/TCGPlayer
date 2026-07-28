# TCGPlayer Automation Platform

A full-stack automation toolkit I built to run my own trading card
reselling business end to end — from pricing and inventory to
marketplace uploads and fulfillment. Originally a set of local scripts,
migrated to a self-hosted cloud deployment so it's accessible from any
device.

## Why I built this
Running a card-selling operation on TCGPlayer involves a lot of
repetitive, error-prone manual work — reconciling duplicate listings,
tracking profit after every batch of sales, reformatting spreadsheets
for upload, and printing shipping materials. I built this platform to
automate that pipeline, then re-architected it for cloud deployment so
I could manage the business remotely instead of from one local machine.

## Features
- **Duplicate card consolidation** — merges duplicate card entries and
  values across CSV exports into clean, accurate records
- **Inventory & profit tracking** — updates sales inventory and profit
  totals automatically after each batch of transactions
- **TCGPlayer upload formatting** — reformats CSV data into the layout
  TCGPlayer's marketplace requires for bulk uploads
- **Real-time processing pipeline** (`/full-process-stream`) — streams
  live progress updates to the browser via Server-Sent Events
- **Automated envelope printing** (`/print-envelopes`) — generates
  properly formatted #10 envelope layouts for order fulfillment
- **Card sorting integration** (`/magic-sorter`) — two-step price upload
  flow that interfaces with a physical card-sorting device
- **Headless browser automation** — Selenium-driven interaction with
  TCGPlayer's marketplace
- **Google API integration** for data sync and reporting

## Tech stack
- **Backend:** Python, Flask
- **Automation:** Selenium, headless Chrome
- **Infra:** Oracle Cloud (Ubuntu VM), deployed as a persistent web service
- **Testing:** pytest (40+ tests covering core logic)
- **Architecture:** business logic (`logic.py`) separated from route
  handling (`app.py`) for testability

## Getting started

1. Clone the repo and install dependencies:
```bash
   pip install -r requirements.txt
```

2. Create a `.env` file in the project root (this file is git-ignored
   and never committed):

FIRST_NAME=YourFirstName
LAST_NAME=YourLastName
STREET_ADDRESS=YourStreetAddress
CITY=YourCity
STATE=YourState
ZIP_CODE=YourZip

TCG_EMAIL=your_email@example.com
TCG_PASSWORD=your_password

TCG_EMAIL_2=your_second_email@example.com
TCG_PASSWORD_2=your_second_password

3. Set your local directories in `constants.py`, or override them via
   environment variables:
```python
   import os
   USER_DIRECTORY = os.path.expanduser("~")
   DOWNLOADS_DIRECTORY = os.path.join(USER_DIRECTORY, "Downloads")
   PROJECT_DIRECTORY = os.path.join(DOWNLOADS_DIRECTORY, "software", "TCGPlayer")
```

4. Run the CLI:
```bash
   python main.py
```
   You'll be shown a numbered menu of available actions (duplicate
   consolidation, inventory/profit updates, upload formatting, etc.) —
   enter the number for the action you'd like to run.

## Notes
This started as local Windows scripts and was re-architected for cloud
deployment — including a full security pass to scrub exposed credentials
from git history and move all secrets to environment variables.
