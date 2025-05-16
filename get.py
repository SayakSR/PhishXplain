import os
import sys
import json
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=chrome_options)

def get_website_data(url):
    driver = setup_driver()
    try:
        driver.get(url)
        time.sleep(5)  # Wait for page to load
        
        # Get all text elements
        text_elements = driver.find_elements(By.XPATH, "//*[text()]")
        text_data = []
        
        for element in text_elements:
            try:
                # Get element's text and location
                text = element.text.strip()
                if text:  # Only include non-empty text
                    location = element.location
                    size = element.size
                    text_data.append({
                        "text": text,
                        "x": location["x"],
                        "y": location["y"],
                        "width": size["width"],
                        "height": size["height"]
                    })
            except:
                continue
        
        # Take screenshot
        screenshot_path = "artifacts/website_screenshot.png"
        os.makedirs("artifacts", exist_ok=True)
        driver.save_screenshot(screenshot_path)
        
        # Save text data
        with open("artifacts/website_text_coordinates.json", "w") as f:
            json.dump(text_data, f, indent=2)
            
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
        
    finally:
        driver.quit()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python get.py <url>")
        sys.exit(1)
        
    url = sys.argv[1]
    success = get_website_data(url)
    sys.exit(0 if success else 1)
