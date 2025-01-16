import os
import logging
from typing import Optional
import requests
from dotenv import load_dotenv
import sys
# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Configure file logging
file_handler = logging.FileHandler('monitoramento_zabbix.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)


# Define the base path for the executable location
if getattr(sys, 'frozen', False):  # Check if the script is running in a bundle (PyInstaller)
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(__file__)

# File to store previously sent alerts
SENT_ALERTS_FILE = os.path.join(base_path, "sent_alerts.txt")

def load_sent_alerts() -> set:
   """Load the set of previously sent alerts from the file."""
   if os.path.exists(SENT_ALERTS_FILE):
       with open(SENT_ALERTS_FILE, 'r', encoding='utf-8') as f:
           return {line.strip() for line in f}
   return set()

def save_sent_alert(alert_id: str) -> None:
   """Save a sent alert to the file."""
   with open(SENT_ALERTS_FILE, 'a', encoding='utf-8') as f:
       f.write(f"{alert_id}\n")

def generate_alert_id(alert: list) -> str:
   """Generate a unique identifier for the alert based on some columns."""
   return f"{alert[0]}-{alert[2]}-{alert[4]}-{alert[5]}"

def send_teams_message(alert: list) -> Optional[requests.Response]:
   """Send an alert message to Microsoft Teams."""
   headers = {"Content-Type": "application/json"}
   body = {
       "Token": os.getenv("TOKEN_TEAMS").strip(),
       "Hora": alert[0],
       "Status": alert[2],
       "Host": alert[4],
       "Incidente": alert[5],
       "Duração": alert[6],
       "Reconhecido": alert[7]
   }
   response = requests.post(os.getenv("URL_TEAMS").strip(), headers=headers, json=body)
   if response.status_code != 202:
       return response
   return None

def main():
    # Load previously sent alerts
    sent_alerts = load_sent_alerts()

    # Initialize Playwright
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--headless=new", "--disable-gpu", "--no-sandbox"], executable_path=f"{os.getenv("BROWSER_PATH")}")
        page = browser.new_page()

        # Access the login page
        logger.info("Accessing the Zabbix login page...")
        page.goto(os.getenv("URL_LOGIN_ZABBIX").strip(), timeout=int(os.getenv("TIMEOUT")))
        
        # Fill in the login form
        logger.info("Filling in the login form...")
        page.locator("xpath=//html/body/main/div[2]/form/ul/li[1]/input").fill(os.getenv("USER_ZABBIX").strip())
        page.locator("xpath=//html/body/main/div[2]/form/ul/li[2]/input").fill(os.getenv("PASS_ZABBIX").strip())
        page.locator("xpath=//html/body/main/div[2]/form/ul/li[4]/button").click()

        page.wait_for_load_state('networkidle')
        logger.info("Accessing the Zabbix dashboard page...")
        page.goto(os.getenv("URL_DASHBOARD_ZABBIX").strip())
        page.wait_for_load_state('networkidle')
        logger.info("Locating rows with high priority alerts...")
        rows = page.locator('tr:has(td.high-bg), tr:has(td.disaster-bg)')
        # Iterate over each row and extract the data
        logger.info(f"Total rows found: {rows.count()}")
        for i in range(rows.count()):
            logger.info(f"Processing row {i + 1} of {rows.count()}...")
            row = rows.nth(i)
            columns = row.locator('td')
            data = [columns.nth(j).inner_text() for j in range(columns.count())]
            if len(data) == 9:
                logger.info(f"Data extracted from row {i + 1}: {data}")
                alert_id = generate_alert_id(data)
                
                logger.info("Sending alert to Teams...")
                # Check if the alert has already been sent
                if alert_id not in sent_alerts:
                    err = send_teams_message(data)
                    if err: 
                        raise Exception("Error sending message to Teams: ", err)
                    
                    # Save the alert as sent
                    save_sent_alert(alert_id)

        # Close the browser
        browser.close()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(e)
        raise e












# import os
# import logging
# from typing import Optional
# import requests
# from dotenv import load_dotenv
# import sys
# import time
# from playwright.sync_api import sync_playwright

# # Load environment variables from .env file
# load_dotenv()

# # Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)
# # Configure file logging
# file_handler = logging.FileHandler('monitoramento_zabbix.log')
# file_handler.setLevel(logging.INFO)
# file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
# logger.addHandler(file_handler)

# # Define the base path for the executable location
# if getattr(sys, 'frozen', False):
#     base_path = os.path.dirname(sys.executable)
# else:
#     base_path = os.path.dirname(__file__)

# # File to store previously sent alerts
# SENT_ALERTS_FILE = os.path.join(base_path, "sent_alerts.txt")

# def load_sent_alerts() -> set:
#     """Load the set of previously sent alerts from the file."""
#     if os.path.exists(SENT_ALERTS_FILE):
#         with open(SENT_ALERTS_FILE, 'r', encoding='utf-8') as f:
#             return {line.strip() for line in f}
#     return set()

# def save_sent_alert(alert_id: str) -> None:
#     """Save a sent alert to the file."""
#     with open(SENT_ALERTS_FILE, 'a', encoding='utf-8') as f:
#         f.write(f"{alert_id}\n")

# def generate_alert_id(alert: list) -> str:
#     """Generate a unique identifier for the alert based on some columns."""
#     return f"{alert[0]}-{alert[2]}-{alert[4]}-{alert[5]}"

# def send_teams_message(alert: list) -> Optional[requests.Response]:
#     """Send an alert message to Microsoft Teams."""
#     headers = {"Content-Type": "application/json"}
#     body = {
#         "Token": os.getenv("TOKEN_TEAMS").strip(),
#         "Hora": alert[0],
#         "Status": alert[2],
#         "Host": alert[4],
#         "Incidente": alert[5],
#         "Duração": alert[6],
#         "Reconhecido": alert[7]
#     }
#     response = requests.post(os.getenv("URL_TEAMS").strip(), headers=headers, json=body)
#     if response.status_code != 202:
#         return response
#     return None

# def launch_browser(playwright):
#     """Launch browser with modified configuration and retry logic."""
#     try:
#         browser_type = getattr(playwright, os.getenv('BROWSER', 'chromium').lower())
#         launch_args = [
#             "--disable-gpu",
#             "--no-sandbox",
#             "--disable-dev-shm-usage",
#             "--disable-setuid-sandbox",
#             "--no-first-run",
#             "--no-zygote",
#             "--single-process",
#             "--headless=new"
#         ]
        
#         browser = browser_type.launch(
#             args=launch_args,
#             timeout=60000,  # Increase timeout to 60 seconds
#             handle_sigint=True,
#             handle_sigterm=True,
#             handle_sighup=True
#         )
#         return browser
#     except Exception as e:
#         logger.error(f"Failed to launch browser: {str(e)}")
#         raise

# def main():
#     # Load previously sent alerts
#     sent_alerts = load_sent_alerts()
#     max_retries = 3
#     retry_count = 0

#     while retry_count < max_retries:
#         try:
#             with sync_playwright() as p:
#                 browser = launch_browser(p)
#                 context = browser.new_context(
#                     viewport={'width': 1920, 'height': 1080},
#                     user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
#                 )
                
#                 page = context.new_page()
#                 page.set_default_timeout(30000)  # Set default timeout to 30 seconds

#                 # Access the login page
#                 logger.info("Accessing the Zabbix login page...")
#                 page.goto(os.getenv("URL_LOGIN_ZABBIX").strip(), timeout=60000)
                
#                 # Fill in the login form
#                 logger.info("Filling in the login form...")
#                 page.locator("xpath=//html/body/main/div[2]/form/ul/li[1]/input").fill(os.getenv("USER_ZABBIX").strip())
#                 page.locator("xpath=//html/body/main/div[2]/form/ul/li[2]/input").fill(os.getenv("PASS_ZABBIX").strip())
#                 page.locator("xpath=//html/body/main/div[2]/form/ul/li[4]/button").click()

#                 # Wait for navigation and load dashboard
#                 page.wait_for_load_state('networkidle')
#                 logger.info("Accessing the Zabbix dashboard page...")
#                 page.goto(os.getenv("URL_DASHBOARD_ZABBIX").strip())
#                 page.wait_for_load_state('networkidle')

#                 # Process alerts
#                 logger.info("Locating rows with high priority alerts...")
#                 rows = page.locator('tr:has(td.high-bg), tr:has(td.disaster-bg)')
                
#                 logger.info(f"Total rows found: {rows.count()}")
#                 for i in range(rows.count()):
#                     logger.info(f"Processing row {i + 1} of {rows.count()}...")
#                     row = rows.nth(i)
#                     columns = row.locator('td')
#                     data = [columns.nth(j).inner_text() for j in range(columns.count())]
                    
#                     if len(data) == 9:
#                         logger.info(f"Data extracted from row {i + 1}: {data}")
#                         alert_id = generate_alert_id(data)
                        
#                         if alert_id not in sent_alerts:
#                             logger.info("Sending alert to Teams...")
#                             err = send_teams_message(data)
#                             if err:
#                                 logger.error(f"Error sending message to Teams: {err}")
#                                 continue
                            
#                             save_sent_alert(alert_id)

#                 # Clean up
#                 context.close()
#                 browser.close()
#                 return  # Success, exit the retry loop
                
#         except Exception as e:
#             logger.error(f"Attempt {retry_count + 1} failed: {str(e)}")
#             retry_count += 1
#             if retry_count >= max_retries:
#                 logger.error("Max retries reached, raising last exception")
#                 raise
#             logger.info(f"Retrying in 5 seconds...")
#             time.sleep(5)

# if __name__ == "__main__":
#     try:
#         main()
#     except Exception as e:
#         logger.error(f"Fatal error: {str(e)}")
#         sys.exit(1)