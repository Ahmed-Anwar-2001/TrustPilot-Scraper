
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Constants ---
CHUNK_SIZE = 20
TARGET_LEADS = 30000

# --- Load previously scraped categories/subcategories ---
# (Assumes a CSV "trustpilot_categories.csv" exists from a prior cell)
categories_df = pd.read_csv("trustpilot_categories.csv")

# --- Setup Selenium ---
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(options=chrome_options)

total_leads = 0     # Total leads collected
chunk_counter = 1   # To number CSV files
leads_chunk = []    # Current chunk of leads

def flush_to_csv(leads, chunk_num):
    """Save the current chunk to a CSV file."""
    df = pd.DataFrame(leads)
    file_name = f"trustpilot_leads_chunk_{chunk_num}.csv"
    df.to_csv(file_name, index=False)
    print(f"Saved chunk {chunk_num} with {len(leads)} records to {file_name}")

# --- Begin scraping business leads ---
# Iterate over each subcategory link
for idx, row in categories_df.iterrows():
    category_link = row["Link"]
    subcategory_name = row["Subcategory"]
    category = row["Category"]
    page = 1
    print(f"Scraping subcategory: '{subcategory_name}' ({category_link})")
    
    while total_leads < TARGET_LEADS:
        # Construct the paginated URL (assumes pagination via ?page=)
        paginated_url = f"{category_link}?page={page}"
        try:
            driver.get(paginated_url)
            time.sleep(2)  # Adjust sleep as needed for page load
        except Exception as e:
            print(f"Error loading page {page} for '{subcategory_name}': {e}")
            break
        
        # Locate all business cards on the page based on the demo structure
        business_cards = driver.find_elements(By.CSS_SELECTOR, "div.styles_wrapper__Jg8fe")
        if not business_cards:
            print(f"No business cards found on page {page} for '{subcategory_name}'.")
            break
        
        # Process each business card
        for card in business_cards:
            if total_leads >= TARGET_LEADS:
                break

            try:
                # Extract Company (business name) from the card
                try:
                    company = card.find_element(By.CSS_SELECTOR, "p.typography_heading-xs__osRhC").text.strip()
                except Exception:
                    company = None
                
                # Extract Name (if available) – fallback to company name
                try:
                    name = card.find_element(By.CSS_SELECTOR, "p.contact-name").text.strip()
                except Exception:
                    name = company
                
                # Extract fields that are displayed on the card
                try:
                    displayed_website = card.find_element(By.CSS_SELECTOR, "p.styles_websiteUrlDisplayed__lSw1A").text.strip()
                except Exception:
                    displayed_website = None
                try:
                    displayed_location = card.find_element(By.CSS_SELECTOR, "span.styles_location__wea8G").text.strip()
                except Exception:
                    displayed_location = None
                
                # --- Click the contact button to reveal the tooltip ---
                try:
                    contact_button = card.find_element(By.CSS_SELECTOR, "button.styles_iconWrapper__offmB")
                    driver.execute_script("arguments[0].click();", contact_button)
                    # Wait up to 5 seconds for the tooltip to appear
                    tooltip = WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "div.tooltip_tooltip__49opG"))
                    )
                    
                    # Extract Email from tooltip (link with data-email-typography attribute)
                    try:
                        email_elem = tooltip.find_element(By.CSS_SELECTOR, "a[data-email-typography]")
                        email = email_elem.get_attribute("href").replace("mailto:", "").strip()
                    except Exception:
                        email = None
                    # Extract Phone from tooltip (link with data-phone-typography attribute)
                    try:
                        phone_elem = tooltip.find_element(By.CSS_SELECTOR, "a[data-phone-typography]")
                        phone = phone_elem.text.strip()
                    except Exception:
                        phone = None
                    # Extract Website from tooltip (link with data-website-typography attribute)
                    try:
                        website_elem = tooltip.find_element(By.CSS_SELECTOR, "a[data-website-typography]")
                        website = website_elem.text.strip()
                    except Exception:
                        website = displayed_website  # Fallback
                    # Extract Address from tooltip
                    try:
                        li_elements = tooltip.find_elements(By.CSS_SELECTOR, "ul.styles_list__2Yton li")
                        address = None
                        for li in li_elements:
                            # If an li does not contain an anchor tag, assume it's the address
                            try:
                                li.find_element(By.TAG_NAME, "a")
                            except Exception:
                                address = li.text.strip()
                                break
                    except Exception:
                        address = displayed_location
                except Exception as e:
                    print(f"Error extracting contact details for '{company}': {e}")
                    email = None
                    phone = None
                    website = displayed_website
                    address = displayed_location

                # Build the lead record with mandatory fields and additional info
                lead = {
                    "Name": name,
                    "Email": email,
                    "Company": company,
                    "Location": address if address else displayed_location,
                    "Phone": phone,
                    "Website": website,
                    "Subcategory": subcategory_name,
                    "Category": category
                }
                leads_chunk.append(lead)
                total_leads += 1
            except Exception as e:
                print(f"Error processing a business card on page {page} for '{subcategory_name}': {e}")
            
            # If chunk size is reached, flush to CSV and clear the chunk
            if len(leads_chunk) >= CHUNK_SIZE:
                flush_to_csv(leads_chunk, chunk_counter)
                chunk_counter += 1
                leads_chunk.clear()
            
            if total_leads >= TARGET_LEADS:
                break
        
        print(f"Subcategory '{subcategory_name}', Page {page}: Total leads scraped so far: {total_leads}")
        page += 1
        if total_leads >= TARGET_LEADS:
            break
    
    if total_leads >= TARGET_LEADS:
        print("Reached target number of leads.")
        break

driver.quit()
# Flush any remaining leads if the final chunk is not full
if leads_chunk:
    flush_to_csv(leads_chunk, chunk_counter)

print(f"Scraping complete. Total leads scraped: {total_leads}")
