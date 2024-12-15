import tkinter as tk
from tkinter import messagebox, scrolledtext
import threading
import schedule
import time
from datetime import datetime
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time

def format_stats(data):
    print(data)
    # Extract relevant fields from the nested "data" dictionary
    relevant_keys = {
        "play_count": "Play Count",
        "digg_count": "Likes",
        "comment_count": "Comment Count",
        "share_count": "Share Count",
        "download_count": "Download Count",
        "collect_count": "Collect Count",
    }
    
    extracted_data = {relevant_keys[key]: data["data"].get(key, 0) for key in relevant_keys}
    
    # Create a formatted string
    formatted_string = ", ".join(f"{key}: {value}" for key, value in extracted_data.items())
    temp = formatted_string.split(',')
    result = {item.split(":")[0].strip(): int(item.split(":")[1].strip()) for item in temp}
    
    return result


def fetch_statistics(url):
    """
    Sends a GET request to the Instatik API and retrieves the statistics object from the JSON response.

    Args:
        url (str): The URL to be passed as a query parameter.

    Returns:
        dict: The 'statistics' object from the response JSON, or None if not found.
    """
    api_url = f"https://tikwm.com/api/?url={url}"
    
    try:
        response = requests.get(api_url)
        time.sleep(1.5)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        data = response.json()
        
        # Extract the 'statistics' objects
        return format_stats(data)
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def authorize_google_sheets(creds_dict, sheet_id):
    """
    Authorizes the Google Sheets API and opens the spreadsheet.

    Args:
        credentials_file (str): Path to the credentials JSON file.
        spreadsheet_name (str): Name of the Google Spreadsheet.

    Returns:
        gspread.Spreadsheet: The authorized spreadsheet object.
    """
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(credentials)
    return client.open_by_key(sheet_id)


def update_spreadsheet(creds_dict, sheet_id):
    """
    Updates the Google Spreadsheet with statistics for each URL.

    Args:
        creds_dict (dict): The credentials JSON as a dictionary.
        sheet_id (str): The ID of the Google Spreadsheet.
    """
    from datetime import datetime

    # Open spreadsheet by ID using creds_dict
    sheet = authorize_google_sheets(creds_dict, sheet_id)
    worksheet = sheet.sheet1

    # Fetch headers from row 3
    headers = worksheet.row_values(3)
    app.log_message("Headers fetched from row 3: " + str(headers))
    print("Headers fetched from row 3:", headers)

    # Find the index of the "URL" column
    try:
        url_col_idx = headers.index("URL") + 1  # Index in gspread is 1-based
    except ValueError:
        raise ValueError("The sheet must have a column header named 'URL' in row 3.")

    # Fetch all rows of the "URL" column
    urls = worksheet.col_values(url_col_idx)[3:]  # Skip the header row (row 3)

    # Add today's date to 6 consecutive free columns in row 3
    today_date = datetime.now().strftime("%Y-%m-%d")
    first_free_col_idx = len(headers) + 1

    # Add today's date 6 times in 6 consecutive columns
    for i in range(6):
        worksheet.update_cell(3, first_free_col_idx + i, today_date)

    # Add Japanese statistic headers
    stat_headers_jp = ["再生数", "いいね数", "コメント数", "シェア数", "ダウンロード数", "コレクション数"]
    for i, header in enumerate(stat_headers_jp):
        worksheet.update_cell(1, first_free_col_idx + i, header)

    # Process each URL
    for i, url in enumerate(urls, start=4):  # Start from row 4 (data starts here)
        if not url:
            continue
        print(f"Fetching statistics for: {url}")
        app.log_message(f"Fetching statistics for: {url}")
        statistics = fetch_statistics(url)
        if statistics:
            stats_values = [
                statistics.get("Play Count", 0),
                statistics.get("Likes", 0),
                statistics.get("Comment Count", 0),
                statistics.get("Share Count", 0),
                statistics.get("Download Count", 0),
                statistics.get("Collect Count", 0),
            ]
            # Update the corresponding cells for each statistic
            for j, value in enumerate(stats_values):
                worksheet.update_cell(i, first_free_col_idx + j, value)
                time.sleep(5)
            print(f"Updated statistics for URL: {url}")
            app.log_message(f"Updating statistics for: {url}")
        else:
            print(f"No statistics found for URL: {url}")



# GUI Application
class TikTokScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TikTok Scraper GUI")
        self.root.geometry("500x400")
        
        # Title
        self.title_label = tk.Label(root, text="TikTok Scraper", font=("Arial", 16))
        self.title_label.pack(pady=10)
        
        # Logs area
        self.logs = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=15, state="disabled")
        self.logs.pack(pady=10)
        
        # Buttons
        self.start_button = tk.Button(root, text="Run Now", command=self.run_script)
        self.start_button.pack(pady=5)
        
        self.exit_button = tk.Button(root, text="Exit", command=self.root.quit)
        self.exit_button.pack(pady=5)
        
        # Schedule the script daily at a specific time (example: 2:00 AM)
        schedule.every().day.at("02:00").do(self.run_script)

        # Start a separate thread for the scheduler
        threading.Thread(target=self.run_scheduler, daemon=True).start()

    def run_script(self):
        # Disable the button while running the script
        self.start_button.config(state="disabled")
        self.log_message("Script execution started...")
        try:
            creds_dict = {
  "type": "service_account",
  "project_id": "astropark",
  "private_key_id": "13b8c3ec85eae7f5e433a46ed06bb17d3a4e2535",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEuwIBADANBgkqhkiG9w0BAQEFAASCBKUwggShAgEAAoIBAQDmOfsTUQQPZaGM\nE5cPfHuMOfs/4Jrm7mtboHbiBxxIeVQ1bWNgul0tpYh8z+nkjfIr2S3wrW5p9B+D\n4lZT5uJo/kaAtE7XN2BSWVT1qJ+MnxFqgVvqpZflMlpMDVXtl+dtvKwr7mJw3txT\nSnOjPwCzGT11S6OhHQugrKhlyxD/J1Py8r+fQ/htG43HzGru/7JaIA6HHj2QdTkV\nf6HraAqWmdPKA6IomQY1DgQ9778p/2gHOhbZd2RYfeeP3Kn7e8p7/sdMjx4/9B5x\nQGxDNTzOYYFYUMWWQ5hUnwUOSZsySWaQ9CVHdktcoiPWDnjBJYPdA3895xwHL8Mr\newiFmckRAgMBAAECgf8bVXNBLgIoeTTU5U1Mhu635iCOaKOsuIk8rdflqlnWNxtU\nqNvNgCuBJM/0i3XoTNSAFmP97MDFWIfRqBUS3CMAgH7FxCxm5dr9dcoFam6G8lH1\nLkQgZBd14UIXQIfrzYv422ZQs2ao8S8ygyHtvVl81mJQqspT1CFyNJdxHAYDp2uT\nKQJu8m37hBaI5l8bfQkJM2ZnftGG2+/mghiUKFbvD7Z7BX3YNPPdlbt3kGPHljDd\nTqWL+aEDSaifHo2FnjJKKDtFQSMcyw0JhojQQuJJRBvjUpSmABP3AS770XtypkMU\nJTHsy+Es4jZ/q57gio+a0Spz0iVW8RXJ7HX7CCkCgYEA9cq13Ag8BbwXp9qBU8uc\nvvFMBESQxG+AWG9PcWsBAl2Z16W0NbVV5lGUXFqKVK48Y79AxsHh1M4GM/Z1uaBz\nGWFz7s0CNN1mCJicQ7zFhHuigtOexl+ULHA9x4Tqbo+u6Xa7xEjHCEnEFijxVfxU\ncZUbG0hICS20Vwu6N56gqKkCgYEA78nHEkKaorQQqsi1Pm/Nn7TpT+ovmIbhlSt3\nuyXo5PPHwnMpg3H+8PQ/aWosZG4xPtdWRecZoM/D7GgBxm3Xow+gnVbFKlLdDFd4\njQJJIHpM4DpHMjyQMnEWX5Gd+9N2oBxgrDTv6ngSGQiPNp2NKLMHPDFW+ixnZ5dM\nCS9GVikCgYBsPbn6zRGJwPx16g78FPXRTLgaRQuvxh6yU0qb+vB11zyRsCJ9aH8M\nr65zQVgb1KM5lhbzsJxAN/6ZUZckiRlG+xiv+E5Zc4qkjHh8iBw/rKazkHgiiiLZ\nsxAx1kHbMKFppOUpmpcz+jBFRgCJylZxsqU+TYWTrTH3B24ZYl0ECQKBgDzi7nJ7\niQphUI4dErB88ShpZojNPTKspSEcfXV+5cklAYcleNgQnRyP2H4q4ITL2iNLyHNN\ngBtuRiCENFcvUv7rm+v3uW7Kxag5mbmsZ+cgRt70zVk7OZ4lSvoPXp8wDcIQEpgH\nhRfzTx0eKEdE8C/ybZbiLGSv273ZFAyM/X4pAoGBAMWQidG7QmfClZIETxKCr5cn\nzWtA71k3NRLggAPkDOL7+5IzMrLrXC3FiGEDa7LVD7yfG4Liyxb5m7fteMX8WFij\n2NP6VzX95xCrDhlKF/PuOQASMCpthlNSIqmmO8weRwvha7nM3TvpdRW5TbD/+FPT\nzYvTXvDGYWbAoCRQWkFX\n-----END PRIVATE KEY-----\n",
  "client_email": "tiktok-scraper@astropark.iam.gserviceaccount.com",
  "client_id": "102588924924089409416",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/tiktok-scraper%40astropark.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
            sheet_id = "1LUOCjXavF86FkrvpSqzCe24L4x05NmOe77zCME-eIGM"
            update_spreadsheet(creds_dict, sheet_id)
            self.log_message("Script executed successfully!")
        except Exception as e:
            self.log_message(f"Error: {e}")
        finally:
            self.start_button.config(state="normal")

    def log_message(self, message):
        # This schedules the log update in the main thread using root.after()
        self.root.after(0, self._log_message, message)

    def _log_message(self, message):
        # Actual log update
        self.logs.config(state="normal")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logs.insert(tk.END, f"{timestamp}: {message}\n")
        self.logs.yview(tk.END)
        self.logs.config(state="disabled")

    def run_scheduler(self):
        while True:
            schedule.run_pending()
            time.sleep(1)


# Main application
if __name__ == "__main__":
    root = tk.Tk()
    app = TikTokScraperApp(root)
    app.log_message("Entry")
    root.mainloop()
