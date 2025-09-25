# Flask Email Open Tracker

A simple yet powerful Flask-based web application to track email opens using a 1x1 transparent pixel. It logs open events directly to a specified Google Sheet in real-time and provides a live dashboard to view the results.

## Features

- **Email Open Tracking**: Embed a unique tracking pixel in your emails to know when they are opened.
- **Real-time Google Sheets Integration**: Automatically updates a Google Sheet with open status, open count, first open time, and last open time.
- **Dynamic Sheet Targeting**: Specify the target Google Spreadsheet and Worksheet directly in the tracking URL.
- **Live Dashboard**: A simple web interface to view the contents of your tracking sheet live.
- **Asynchronous Updates**: Google Sheet updates are handled in a background thread to ensure the tracking pixel loads instantly without delay.
- **Deployment Ready**: Designed to be easily deployed on platforms like Render or Heroku using environment variables.
- **Robust Authentication**: Securely handles Google API credentials, including multi-line private keys, for seamless deployment.

## How It Works

1.  **Embed Pixel**: You embed a small, invisible 1x1 GIF image in the HTML of your outgoing email. The `src` of this image points to this application's tracking endpoint.
2.  **URL Parameters**: The tracking URL is crafted to include the name of the target Google Spreadsheet, the specific Worksheet, and a unique identifier for the recipient (usually their email address).
3.  **Track Request**: When the recipient opens the email, their email client requests the image from your server.
4.  **Log the Open**: The Flask application receives the request, logs the open event, and immediately sends back the 1x1 pixel image as a response.
5.  **Update Sheet**: In a background process, the application authenticates with the Google Sheets API, finds the row corresponding to the user's email, and updates the relevant columns (`Status`, `Open Count`, `First Opened`, `Last Opened`).

## Setup and Installation

### 1. Prerequisites

- Python 3.7+
- A Google Cloud Platform (GCP) account
- A deployment platform like Render (or a local server for testing)

### 2. Google Cloud Project Setup

1.  **Create a GCP Project**: Go to the Google Cloud Console and create a new project.
2.  **Enable APIs**: In your project, navigate to "APIs & Services" > "Library" and enable the following APIs:
    - **Google Drive API**
    - **Google Sheets API**
3.  **Create a Service Account**:
    - Go to "APIs & Services" > "Credentials".
    - Click "Create Credentials" and select "Service account".
    - Give it a name (e.g., "sheets-updater") and grant it the "Editor" role for now (you can refine this later).
    - Click "Done".
4.  **Generate a JSON Key**:
    - Find your newly created service account in the "Credentials" list and click on it.
    - Go to the "KEYS" tab, click "ADD KEY", and choose "Create new key".
    - Select **JSON** as the key type and click "CREATE". A JSON file will be downloaded. **Keep this file secure!**

### 3. Google Sheet Preparation

1.  **Create a Google Sheet**: This will be your tracking database.
2.  **Share the Sheet**: Click the "Share" button in your Google Sheet and share it with the `client_email` address found in the JSON key file you just downloaded. Grant it **Editor** permissions.
3.  **Add Headers and Data**: The application expects the sheet to have specific headers. At a minimum, you must have an `email` column that you pre-populate with the email addresses of the recipients you want to track. The script will automatically add all required headers if they are missing.

    *Example Sheet Structure:*
    | name | email | Send Status | Time | Status | Open Count | First Opened | Last Opened |
    |---|---|---|---|---|---|---|---|
    | John Doe | john.doe@example.com | Sent | | | | | |
    | Jane Smith | jane.smith@example.com | Sent | | | | | |

### 4. Application Setup

1.  **Clone the Repository**:
    ```bash
    git clone <your-repository-url>
    cd email_tracker
    ```

2.  **Create a Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install Dependencies**: Create a `requirements.txt` file with the following content:
    ```txt
    Flask
    gspread
    oauth2client
    pytz
    gunicorn
    # psycopg2-binary # Optional, if using the database feature
    ```
    Then install them:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**:
    The application uses environment variables for configuration, which is ideal for deployment.

    - From your downloaded GCP JSON key file, get the following values:
      - `project_id` -> `GCP_PROJECT_ID`
      - `private_key_id` -> `GCP_PRIVATE_KEY_ID`
      - `client_email` -> `GCP_CLIENT_EMAIL`
      - `client_id` -> `GCP_CLIENT_ID`
      - `private_key` -> This needs special handling.

    - **Handling the Private Key**: The `private_key` is a multi-line string that can cause issues in some environments. The recommended approach is to Base64 encode it.

      - **Linux/macOS**:
        ```bash
        # Copy the private key from the JSON file, including "-----BEGIN..." and "-----END..."
        echo "PASTE_YOUR_PRIVATE_KEY_HERE" | base64
        ```
      - **Online Tool**: Use a trusted online Base64 encoder.

      - Create an environment variable `GCP_PRIVATE_KEY_B64` with the resulting Base64 string.

## Usage

### Running Locally

Set the environment variables in your terminal and run the app.

```bash
# Example for Linux/macOS
export GCP_PROJECT_ID="your-project-id"
export GCP_PRIVATE_KEY_ID="your-key-id"
export GCP_CLIENT_EMAIL="your-service-account-email"
export GCP_CLIENT_ID="your-client-id"
export GCP_PRIVATE_KEY_B64="your-base64-encoded-key"

python app.py
```
The app will run on `http://localhost:5000`.

### Tracking URL Format

The URL for the tracking pixel follows this structure:
`http://<your-app-url>/track/<spreadsheet_name>/<worksheet_name>/<user_email>`

- **spreadsheet_name**: The exact name of your Google Spreadsheet.
- **worksheet_name**: The name of the worksheet (tab) within that spreadsheet.
- **user_email**: The email of the recipient, which must match an entry in the `email` column of your sheet.

**Example HTML for Email:**

```html
<p>Hello!</p>
<p>This is an important message.</p>

<!-- Tracking Pixel -->
<img src="https://your-app-name.onrender.com/track/Q4-Campaign/Leads/john.doe@example.com" width="1" height="1" alt="">
```

### Dashboard URL Format

To view the live data from your sheet, use the following URL:
`http://<your-app-url>/dashboard/<spreadsheet_name>/<worksheet_name>`

**Example:**
`https://your-app-name.onrender.com/dashboard/Q4-Campaign/Leads`

## Deployment on Render

1.  Push your code to a GitHub repository.
2.  Create a new "Web Service" on Render and connect it to your repository.
3.  Set the **Build Command** to: `pip install -r requirements.txt`
4.  Set the **Start Command** to: `gunicorn app:app`
5.  Under the "Environment" tab, add all the `GCP_*` environment variables as configured above, including `GCP_PRIVATE_KEY_B64`.
6.  Deploy! Your service will be live at the URL provided by Render.


