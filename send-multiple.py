import gspread
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import os
import requests

# ----------------------- Google Sheets Setup -----------------------

# Define the scope and credentials for Google Sheets API
SCOPE = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]
SERVICE_ACCOUNT_FILE = 'service_account.json'  # Path to your service account JSON file

# Authenticate and initialize the Google Sheets client
credentials = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, SCOPE)
gc = gspread.authorize(credentials)

# Specify the Google Sheet and Worksheet names
SHEET_NAME = 'DATA KURSI WORSHIP NIGHT'
WORKSHEET_NAME = 'SENDQUEUE'  # Worksheet containing the send queue

try:
    sh = gc.open(SHEET_NAME)
    worksheet = sh.worksheet(WORKSHEET_NAME)
    print(f"Successfully accessed the worksheet: {WORKSHEET_NAME}")
except Exception as e:
    print(f"Error accessing Google Sheet: {e}")
    exit(1)

# ----------------------- Selenium Setup -----------------------

def initialize_driver():
    """
    Initialize the Selenium WebDriver with Chrome options.
    Uses a persistent user data directory to retain WhatsApp sessions.
    """
    
    # chrome_options.add_argument("--headless")  # Uncomment to run in headless mode (no GUI)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    return driver

# ----------------------- Utility Functions -----------------------

def download_image(image_url, save_path):
    """
    Downloads an image from the specified URL and saves it to the given path.
    """
    try:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            print(f"Image downloaded to {save_path}")
            return save_path
        else:
            print(f"Failed to download image. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None

def send_whatsapp_image(driver, phone_number, image_path, caption=""):
    """
    Sends an image via WhatsApp Web to the specified phone number with an optional caption.
    """
    url = f"https://web.whatsapp.com/send?phone={phone_number}"
    driver.get(url)
    
    try:
        # Wait until the chat interface loads
        chat_xpath = '//div[@contenteditable="true"][@data-tab="3"]'
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, chat_xpath))
        )
        print(f"Chat loaded successfully for {phone_number}")
        
        # Click on the attachment (paperclip) icon
        attachment_xpath = '//div[@title="Attach"]'
        attachment_box = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, attachment_xpath))
        )
        attachment_box.click()
        print("Clicked on the attachment icon.")
        
        # Click on the image/video input
        image_input_xpath = '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]'
        image_box = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, image_input_xpath))
        )
        
        # Upload the image
        image_box.send_keys(image_path)
        print(f"Uploaded the image from {image_path}")
        
        # Wait for the image preview to appear
        time.sleep(10)
        
        if caption:
            # Find the caption box and enter the caption
            caption_xpath = '//div[@contenteditable="true"][@data-tab="10"]'
            caption_box = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, caption_xpath))
            )
            caption_box.send_keys(caption)
            print("Added caption to the image.")
        
        # Click the send button
        send_button_xpath = '//span[@data-icon="send"]'
        send_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, send_button_xpath))
        )
        send_button.click()
        print(f"Image sent to {phone_number}")
        # Wait for the image to send
        time.sleep(15)
        return True
    except Exception as e:
        print(f"Failed to send image to {phone_number}: {e}")
        return False

def send_whatsapp_images(driver, phone_number, image_paths, caption=""):
    """
    Sends multiple images via WhatsApp Web to the specified phone number with an optional caption.
    """
    url = f"https://web.whatsapp.com/send?phone={phone_number}"
    driver.get(url)
    
    try:
        # Wait until the chat interface loads
        chat_xpath = '//div[@contenteditable="true"][@data-tab="3"]'
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, chat_xpath))
        )
        print(f"Chat loaded successfully for {phone_number}")
        
        # Click on the attachment (paperclip) icon
        attachment_xpath = '//div[@title="Attach"]'
        attachment_box = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, attachment_xpath))
        )
        attachment_box.click()
        print("Clicked on the attachment icon.")
        
        # Click on the image/video input
        image_input_xpath = '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]'
        image_box = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, image_input_xpath))
        )
        
        # Upload all images
        image_paths_str = '\n'.join(image_paths)
        image_box.send_keys(image_paths_str)
        print(f"Uploaded images: {image_paths}")
        
        # Wait for the image previews to appear
        time.sleep(10)
        
        if caption:
            # Find the caption box and enter the caption
            caption_xpath = '//div[@contenteditable="true"][@data-tab="10"]'
            caption_boxes = driver.find_elements(By.XPATH, caption_xpath)
            # If multiple images, the last caption box corresponds to the last image
            for caption_box in caption_boxes:
                caption_box.send_keys(caption)
            print("Added caption to the images.")
        
        # Click the send button
        send_button_xpath = '//span[@data-icon="send"]'
        send_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, send_button_xpath))
        )
        send_button.click()
        print(f"Images sent to {phone_number}")
        # Wait for the images to send
        time.sleep(15)
        return True
    except Exception as e:
        print(f"Failed to send images to {phone_number}: {e}")
        return False

def process_send_queue(driver, worksheet):
    """
    Processes entries in the SENDQUEUE worksheet:
    - Groups image IDs by phone number
    - Downloads all images for each phone number
    - Sends them together via WhatsApp
    - Removes the entries from the sheet upon success
    """
    try:
        # Fetch all values from the worksheet
        rows = worksheet.get_all_values()

        # Check if the sheet is empty
        if not rows:
            print("SENDQUEUE is empty. No messages to send.")
            return

        # Build a dictionary to group image IDs by phone number
        send_dict = {}
        for idx, row in enumerate(rows, start=1):  # gspread uses 1-based indexing
            # Ensure that there are at least two columns
            if len(row) < 2:
                print(f"Row {idx} does not have enough columns. Skipping.")
                continue

            image_id = row[0].strip()
            phone_number = row[1].strip()

            if not image_id or not phone_number:
                print(f"Row {idx} is missing data. Skipping.")
                continue

            if phone_number not in send_dict:
                send_dict[phone_number] = {'image_ids': [], 'row_indices': []}

            send_dict[phone_number]['image_ids'].append(image_id)
            send_dict[phone_number]['row_indices'].append(idx)

        # List to collect all rows to delete after processing
        all_rows_to_delete = []

        # Process each phone number
        for phone_number, data in send_dict.items():
            image_ids = data['image_ids']
            row_indices = data['row_indices']

            # Download all images for this phone number
            image_paths = []
            for image_id in image_ids:
                image_url = f"http://188.166.223.224/ticket/{image_id}.png"
                image_name = f"{image_id}.png"
                image_path = os.path.join(os.getcwd(), image_name)
                downloaded_image = download_image(image_url, image_path)

                if downloaded_image:
                    image_paths.append(downloaded_image)
                else:
                    print(f"Image {image_id} could not be downloaded. Skipping phone number {phone_number}.")
                    break  # Skip sending to this phone number if any image fails to download
            else:
                # Send all images together via WhatsApp
                success = send_whatsapp_images(driver, phone_number, image_paths)

                if success:
                    # Collect the rows to delete
                    all_rows_to_delete.extend(row_indices)
                    print(f"Scheduled rows {row_indices} for deletion.")

                    # Delete the downloaded images
                    for image_path in image_paths:
                        try:
                            os.remove(image_path)
                            print(f"Deleted the image file: {image_path}")
                        except Exception as e:
                            print(f"Could not delete the image file: {e}")

                    # Short delay to prevent triggering spam filters
                    time.sleep(5)
                else:
                    print(f"Failed to send images to {phone_number}. Will retry in the next cycle.")

        # Delete all rows after processing
        if all_rows_to_delete:
            # Sort the list in reverse order to prevent index shifting issues
            for idx in sorted(all_rows_to_delete, reverse=True):
                worksheet.delete_rows(idx)
                print(f"Row {idx} deleted from SENDQUEUE.")
        else:
            print("No rows to delete.")

    except Exception as e:
        print(f"An error occurred while processing SENDQUEUE: {e}")


# ----------------------- Main Function -----------------------

def main():
    # Initialize Selenium WebDriver
    driver = initialize_driver()
    
    # Open WhatsApp Web
    driver.get('https://web.whatsapp.com')
    print("Please scan the QR code to log in to WhatsApp Web.")
    
    try:
        # Wait until the main page is loaded by checking for the chat search box
        search_xpath = '//div[@contenteditable="true"][@data-tab="3"]'
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, search_xpath))
        )
        print("Logged in to WhatsApp Web successfully.")
    except Exception as e:
        print(f"Error logging in to WhatsApp Web: {e}")
        driver.quit()
        return
    
    try:
        while True:
            print("\nChecking SENDQUEUE for new messages...")
            process_send_queue(driver, worksheet)
            print("Cycle complete. Waiting for the next check...")
            time.sleep(30)  # Wait for 30 seconds before checking again
    except KeyboardInterrupt:
        print("\nScript interrupted by user. Closing the browser.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
