from langchain.tools import Tool
from langchain.agents import initialize_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# ✅ Initialize AI Agent
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key="AIzaSyDkIKB5VaUERkbgdCVXAUyjInuy6OYf9KM")

# ✅ Define a Web Scraping Function
def scrape_supermarket(url, search_query):
    options = Options()
    options.add_argument("--headless")  # ✅ Run Chrome in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920x1080")

    service = Service()  # ✅ Service instance for WebDriver
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)  # ✅ Explicit wait

        # ✅ Handle cookie consent popup (if present)
        try:
            cookie_popup = wait.until(EC.presence_of_element_located((By.ID, "cookiespool-shadow-background")))
            driver.execute_script("arguments[0].remove();", cookie_popup)  # Remove the overlay using JavaScript
            print("🍪 Cookie popup detected and removed.")
        except:
            print("✅ No cookie popup detected.")

        # ✅ Find the search box and enter the query
        search_box = wait.until(EC.presence_of_element_located((By.ID, "js-site-search-input")))
        search_box.clear()
        search_box.send_keys(search_query)

        # ✅ Wait for the search button and click it
        search_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "js-search-validate")))
        driver.execute_script("arguments[0].click();", search_button)  # Click via JavaScript to avoid intercept issues
        print("🔍 Search button clicked.")

        # ✅ Wait for the first product result to appear
        first_product_element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "item-name")))
        product_name = first_product_element.text.strip()
        print(f"🔹 Found Product: {product_name}")  # ✅ Print found product

        # ✅ Find the first product price
        first_price_element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "item-price")))
        product_price = first_price_element.text.strip()
        print(f"💰 Found Price: {product_price}")  # ✅ Print found price

        result = f"{product_name} - {product_price}"

    except Exception as e:
        print(f"❌ ERROR: {e}")
        result = "No results found."

    finally:
        driver.quit()  # ✅ Close the browser

    return result

# ✅ Define AI Tool for Searching Prices
search_tool = Tool(
    name="Supermarket Price Search",
    func=lambda query: scrape_supermarket("https://www.carrefoursa.com", query),
    description="Searches Carrefour for product prices in Turkish."
)

# ✅ Modify AI Agent to use Turkish alternative words
agent_prompt = """You are an AI assistant helping to find supermarket prices. 
If the product is not found, try searching for Turkish alternatives. 
For example, instead of 'milk', use 'süt'. Instead of 'cheese', use 'peynir'. 
Your searches must always be in Turkish.
"""

# ✅ Create the AI Agent
agent = initialize_agent(
    tools=[search_tool],
    llm=llm,
    agent="zero-shot-react-description",
    verbose=True,
    agent_kwargs={"system_message": agent_prompt}
)

# ✅ Ask AI to find a product price
product = "Pınar 1 litre süt"  # ✅ Use Turkish word
result = agent.invoke({"input": f"Find the price of {product} in Carrefour."})

print(f"🛒 Final Result: {result}")
