

import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Configure Selenium to run headless
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")

# Initialize the Chrome WebDriver (adjust executable_path if needed)
driver = webdriver.Chrome(options=chrome_options)

# Load the Trustpilot categories page
categories_url = "https://uk.trustpilot.com/categories"
driver.get(categories_url)
time.sleep(3)  # Allow the page to load

# Find all category cards; these cards have a unique class (adjust if needed)
category_cards = driver.find_elements(By.CSS_SELECTOR, "div.styles_card__Z1lPe")
categories_data = []

for card in category_cards:
    try:
        # Extract the parent category type from the heading element
        cat_type_elem = card.find_element(By.CSS_SELECTOR, "h2.styles_headingDisplayName__XN7x3")
        category_type = cat_type_elem.text.strip()
    except Exception as e:
        category_type = None
        
    try:
        # Locate the list of subcategories within this card.
        # Each subcategory is an <a> tag inside the <ul> with class styles_linkList__C9GRA.
        subcat_elements = card.find_elements(By.CSS_SELECTOR, "ul.styles_linkList__C9GRA li a")
        for subcat in subcat_elements:
            subcat_name = subcat.text.strip()
            subcat_href = subcat.get_attribute("href")
            # If the link is relative, prefix with the base URL.
            if subcat_href.startswith("/"):
                subcat_link = "https://uk.trustpilot.com" + subcat_href
            else:
                subcat_link = subcat_href
            categories_data.append({
                "Link": subcat_link,
                "Subcategory": subcat_name,
                "Category": category_type
            })
    except Exception as e:
        print(f"Error processing a category card: {e}")

# Save the collected category/subcategory links to CSV
df_categories = pd.DataFrame(categories_data)
df_categories.to_csv("trustpilot_categories.csv", index=False)
print(f"Collected {len(df_categories)} category links. Saved to trustpilot_categories.csv")

driver.quit()
