from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

# ✅ Initialize AI Model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key="AIzaSyDkIKB5VaUERkbgdCVXAUyjInuy6OYf9KM"
)

# ✅ Common Browser Configuration
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Prevent bot detection
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# ✅ Custom Agent Prompt (Ensures Correct Language & Structure)
agent_prompt = """You are a smart price comparison assistant.
- When searching Carrefour, **only use Turkish words**.
- When searching AH.nl, **only use Dutch words**.
- If no result is found, think of **alternative words in the same language** (e.g., synonyms, related words).
- Try a maximum of **3 alternative search terms** before stopping.
- Extract the **first product’s name and price** from the list.
- Display the **product name and price** in a structured format.
"""

# ✅ Supermarket Scraper (CarrefourSA & AH.nl)
def scrape_supermarket(url, search_query, supermarket, attempt=1):
    if attempt > 3:
        print("❌ Maximum search attempts reached. Stopping.")
        return f"No product found in {supermarket}."

    driver = setup_driver()
    driver.get(url)

    # 🏪 **CarrefourSA**
    if supermarket == "Carrefour":
        print(f"🔍 Searching Carrefour for: {search_query}")

        # Handle Cookie Popup
        try:
            cookie_popup = driver.find_element(By.ID, "onetrust-accept-btn-handler")
            cookie_popup.click()
            print("🍪 Cookie popup removed.")
        except:
            print("✅ No cookie popup.")

        # ✅ **Fixed Carrefour Search Logic**
        try:
            search_box = driver.find_element(By.ID, "js-site-search-input")
            search_box.send_keys(search_query)
            driver.find_element(By.CLASS_NAME, "js-search-validate").click()  # ✅ Click search button
            time.sleep(5)

            # Extract first product details
            first_product = driver.find_element(By.CLASS_NAME, "item-name").text
            product_price = driver.find_element(By.CLASS_NAME, "item-price").text
            print(f"🔹 Found Product: {first_product}")
            print(f"💰 Found Price: {product_price}")
            driver.quit()
            return f"{first_product} - {product_price}"
        except:
            print(f"❌ No product found. Asking AI for an alternative search term... (Attempt {attempt}/3)")
            driver.quit()
            alternative_term = llm.invoke(f"Suggest a related Turkish search term for {search_query} (only return the word)").strip()
            return scrape_supermarket(url, alternative_term, supermarket, attempt + 1)

    # 🇳🇱 **Albert Heijn (AH.nl)**
    elif supermarket == "AH":
        print(f"🔍 Searching AH for: {search_query}")

        # Perform Search
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

            print(f"🔹 Found Product: {first_product}")
            print(f"💰 Found Price: {product_price}")
            driver.quit()
            return f"{first_product} - {product_price}"
        except:
            print(f"❌ No product found. Asking AI for an alternative search term... (Attempt {attempt}/3)")
            driver.quit()
            alternative_term = llm.invoke({"input": f"Suggest a related Dutch search term for {search_query} (only return the word)"}).content.strip()
            return scrape_supermarket(url, alternative_term, supermarket, attempt + 1)

    driver.quit()
    return f"No product found in {supermarket}."

# ✅ Define AI Tools for Carrefour & AH
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

# ✅ Create the AI Agent with Custom Prompt
agent = initialize_agent(
    tools=[carrefour_tool, ah_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    agent_kwargs={"system_message": agent_prompt}  # 🔥 Custom Prompt
)

# ✅ Ask AI to find product prices
product_carrefour = "Pınar 1 litre süt"
product_ah = "Arla volle melk"

print("\n🔍 **Searching CarrefourSA...**")
result_carrefour = agent.invoke({"input": f"Find the price of {product_carrefour} in Carrefour."})
print(f"🛒 Carrefour Result: {result_carrefour}")

print("\n🔍 **Searching Albert Heijn (AH.nl)...**")
result_ah = agent.invoke({"input": f"Find the price of {product_ah} in AH."})
print(f"🛒 AH Result: {result_ah}")
