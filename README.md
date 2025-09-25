# Email Tracker

This project is an Email Tracker application that logs and tracks email activity, and can push data to a Google Spreadsheet using the `gspread` library.

## Features
- Track email activity and log data
- Update or insert data into a Google Spreadsheet
- Dashboard for viewing tracked data

## Files
- `app.py`: Main application logic
- `index.py`: Entry point or additional logic
- `my_action.py`: Contains custom actions or business logic
- `dashboard.html`: Dashboard UI for viewing tracked data
- `email.html`: Email template or UI
- `data.txt`: Stores local data logs
- `requirements.txt`: Python dependencies

## Setup
1. **Clone the repository**
2. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```
3. **Google Sheets Setup:**
   - Create a Google Cloud project and enable the Google Sheets API.
   - Download your `credentials.json` and place it in the project directory.
   - Share your Google Sheet with the service account email from the credentials.
4. **Run the application:**
   ```powershell
   python app.py
   ```

## Usage
- The app will track email activity and update the Google Sheet.
- If a user/email is not found in the sheet, a new row will be added.
- View the dashboard at `dashboard.html` for a summary.

## Requirements
- Python 3.x
- gspread
- Flask (if used for web dashboard)
- Google-auth

## License
MIT License
