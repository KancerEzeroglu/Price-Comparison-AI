from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time

# ✅ Initialize AI Model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key="AIzaSyDkIKB5VaUERkbgdCVXAUyjInuy6OYf9KM"
)

# ✅ Custom Agent Prompt (Ensures Correct Language & Structure)
agent_prompt = """You are a smart price comparison assistant.
- When searching Carrefour, **only use Turkish words**.
- When searching AH.nl, **only use Dutch words**.
- If no result is found, try **alternative words in the same language**.
- Extract the **first product’s name and price** from the list.
- Display the **product name and price** in a structured format.
"""

# ✅ Supermarket Search Function (Carrefour & AH)
def scrape_supermarket(url, search_query, supermarket):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(url)

    # 🏪 **CarrefourSA**
    if supermarket == "Carrefour":
        print(f"🔍 Searching Carrefour for: {search_query}")

        # Handle Cookie Popup
        try:
            cookie_popup = driver.find_element(By.ID, "cookiespool-shadow-background")
            driver.execute_script("arguments[0].remove();", cookie_popup)
            print("🍪 Cookie popup removed.")
        except:
            pass

        # Perform Search
        search_box = driver.find_element(By.ID, "js-site-search-input")
        search_box.send_keys(search_query)
        driver.find_element(By.CLASS_NAME, "js-search-validate").click()
        time.sleep(5)

        # Extract first product details
        try:
            first_product = driver.find_element(By.CLASS_NAME, "item-name").text
            product_price = driver.find_element(By.CLASS_NAME, "item-price").text
            print(f"🔹 Found Product: {first_product}")
            print(f"💰 Found Price: {product_price}")
            return f"{first_product} - {product_price}"
        except:
            print("❌ No product found, trying alternative Turkish search terms...")
            return scrape_supermarket(url, "süt litre", supermarket)  # Try alternative

    # 🇳🇱 **Albert Heijn (AH.nl)**
    elif supermarket == "AH":
        print(f"🔍 Searching AH for: {search_query}")

        # Perform Search
        search_box = driver.find_element(By.ID, "navigation-search-input")
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.RETURN)  # ✅ Simulate pressing Enter instead of clicking
        time.sleep(5)

        # Extract first product details
        try:
            first_product = driver.find_element(By.CLASS_NAME, "line-clamp_lineClamp__2lnzv").text
            price_integer = driver.find_element(By.CLASS_NAME, "price-amount_integer__+e2XO").text
            price_fraction = driver.find_element(By.CLASS_NAME, "price-amount_fractional__kjJ7u").text
            product_price = f"€{price_integer}.{price_fraction}"
            print(f"🔹 Found Product: {first_product}")
            print(f"💰 Found Price: {product_price}")
            return f"{first_product} - {product_price}"
        except:
            print("❌ No product found, trying alternative Dutch search terms...")
            return scrape_supermarket(url, "melk", supermarket)  # Try alternative

    driver.quit()


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

result_carrefour = agent.invoke({"input": f"Find the price of {product_carrefour} in Carrefour."})
result_ah = agent.invoke({"input": f"Find the price of {product_ah} in AH."})

print("🛒 Carrefour Result:", result_carrefour)
print("🛒 AH Result:", result_ah)
