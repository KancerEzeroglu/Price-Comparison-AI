import csv
import time
import datetime
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import re

# ✅ Initialize AI Model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key="AIzaSyDkIKB5VaUERkbgdCVXAUyjInuy6OYf9KM"
)

# ✅ Get Current Date for CSV
current_date = datetime.datetime.now().strftime("%Y-%m-%d")

# ✅ Configure Browser
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Prevent bot detection
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# ✅ Custom Agent Prompt
agent_prompt = """You are a smart price comparison assistant.
- When searching Carrefour, **only use Turkish words**.
- When searching AH.nl, **only use Dutch words**.
- If no result is found, think of **alternative words in the same language**.
- Try a maximum of **3 alternative search terms** before stopping.
- Extract the **first product’s name and price** from the list.
- Log all search steps and save results to a CSV file.
"""

# ✅ Scraper Function (Handles Carrefour & AH.nl)
def scrape_supermarket(url, search_query, supermarket, attempt=1):
    if attempt > 3:
        print("❌ Maximum search attempts reached. Stopping.")
        return None, None

    driver = setup_driver()
    driver.get(url)

    if supermarket == "Carrefour":
        print(f"🔍 Searching Carrefour for: {search_query}")

        # Handle Cookie Popup
        try:
            cookie_popup = driver.find_element(By.ID, "onetrust-accept-btn-handler")
            cookie_popup.click()
            print("🍪 Cookie popup removed.")
        except:
            print("✅ No cookie popup.")

        # ✅ **Search Carrefour**
        try:
            search_box = driver.find_element(By.ID, "js-site-search-input")
            search_box.send_keys(search_query)
            driver.find_element(By.CLASS_NAME, "js-search-validate").click()
            time.sleep(5)

            # Extract first product details
            first_product = driver.find_element(By.CLASS_NAME, "item-name").text
            product_price = driver.find_element(By.CLASS_NAME, "item-price").text
            print(f"🔹 Found Product: {first_product} - 💰 {product_price}")
            driver.quit()
            return first_product, product_price
        except:
            print(f"❌ No product found. Asking AI for an alternative search term... (Attempt {attempt}/3)")
            driver.quit()
            alternative_term = llm.invoke(f"Suggest a related Turkish search term for {search_query} (only return the word)").strip()
            return scrape_supermarket(url, alternative_term, supermarket, attempt + 1)

    elif supermarket == "AH":
        print(f"🔍 Searching AH for: {search_query}")
        
        try:
            search_box = driver.find_element(By.ID, "navigation-search-input")
            search_box.send_keys(search_query)
            search_box.send_keys(Keys.RETURN)  # ✅ Simulate pressing Enter instead of clicking
            time.sleep(5)

            # ✅ **AH Product Extraction Using `data-testhook` or XPath**
            try:
                first_product = driver.find_element(By.CSS_SELECTOR, "[data-testhook='product-title']").text
            except:
                first_product = driver.find_element(By.XPATH, "//strong[contains(@class, 'product-card-portrait_title')]").text

            # ✅ **AH Price Extraction**
            try:
                price_integer = driver.find_element(By.CSS_SELECTOR, "[data-testhook='price-amount'] .price-amount_integer__+e2XO").text
                price_fraction = driver.find_element(By.CSS_SELECTOR, "[data-testhook='price-amount'] .price-amount_fractional__kjJ7u").text
            except:
                price_integer = driver.find_element(By.XPATH, "//span[contains(@class, 'price-amount_integer')]").text
                price_fraction = driver.find_element(By.XPATH, "//span[contains(@class, 'price-amount_fractional')]").text

            product_price = f"€{price_integer}.{price_fraction}"

            print(f"🔹 Found Product: {first_product} - 💰 {product_price}")
            driver.quit()
            return first_product, product_price
        
        except:
            print(f"❌ No product found. Asking AI for an alternative search term... (Attempt {attempt}/3)")
            driver.quit()
            alternative_term = llm.invoke({"input": f"Suggest a related Dutch search term for {search_query} (only return the word)"}).content.strip()
            return scrape_supermarket(url, alternative_term, supermarket, attempt + 1)

    driver.quit()
    return None, None

# ✅ Define AI Tools
carrefour_tool = Tool(
    name="Carrefour Price Search",
    func=lambda query: scrape_supermarket("https://www.carrefoursa.com", query, "Carrefour"),
    description="Searches Carrefour for product prices."
)

ah_tool = Tool(
    name="AH Price Search",
    func=lambda query: scrape_supermarket("https://www.ah.nl", query, "AH"),
    description="Searches Albert Heijn (AH.nl) for product prices."
)

# ✅ Initialize Agent
agent = initialize_agent(
    tools=[carrefour_tool, ah_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    agent_kwargs={"system_message": agent_prompt}
)

# ✅ Search Queries
carrefour_keywords = ["Pınar 1 litre süt", "normal ekmek", "1kg Dana Kıyma", "1kg Un", "Ayçiçek Yağı 1 Litre", "10 Adet Yumurta", "kapya biber kg"]
ah_keywords = ["Arla volle melk", "AH Vloerbrood wit heel", "1kg Rundergehakt", "1kg meel", "1lt Zonnebloemolie", "eieren 10", "Sweet palermo rode puntpaprika 250gr"]

# ✅ CSV File Setup with Date
csv_filename = f"supermarket_prices_{current_date}.csv"

# ✅ Open CSV and Collect Data
with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Date Collected", "Supermarket", "Search Query", "Product Name", "Price"])

    # ✅ Search Carrefour Keywords
    for keyword in carrefour_keywords:
        result = agent.invoke({"input": f"Find the price of {keyword} in Carrefour."})
        response_text = result["output"]

        # ✅ Extract Product Name & Price from AI Output
        match = re.search(r"(.+?) in Carrefour is (.+?)\.", response_text)
        if match:
            product_name, price = match.groups()
            writer.writerow([current_date, "Carrefour", keyword, product_name.strip(), price.strip()])
        else:
            print(f"⚠ Unable to parse Carrefour response: {response_text}")

    # ✅ Search AH Keywords
    for keyword in ah_keywords:
        result = agent.invoke({"input": f"Find the price of {keyword} in AH."})
        response_text = result["output"]

        # ✅ Extract Product Name & Price from AI Output
        match = re.search(r"(.+?) in AH is (.+?)\.", response_text)
        if match:
            product_name, price = match.groups()
            writer.writerow([current_date, "Albert Heijn", keyword, product_name.strip(), price.strip()])
        else:
            print(f"⚠ Unable to parse AH response: {response_text}")

print(f"✅ Data saved to {csv_filename}")
