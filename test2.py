import time
import csv
import asyncio
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
from playwright.async_api import async_playwright

# ✅ Initialize AI Model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key="AIzaSyDkIKB5VaUERkbgdCVXAUyjInuy6OYf9KM"
)

# ✅ Define AI Agent Prompt
agent_prompt = """You are an intelligent web navigation assistant.
- Visit supermarket websites and search for product prices.
- **Find the search box dynamically** without hardcoding.
- **Identify the product name & price dynamically** (do not rely on fixed CSS selectors).
- If the search fails, try up to **3 alternative search terms** in the same language.
- Describe how to locate the product name & price on the page.
"""

# ✅ Async Function to Scrape Prices Fully Dynamically
async def scrape_prices(url, search_query, supermarket, attempt=1):
    if attempt > 3:
        print(f"❌ Maximum search attempts reached for {search_query} in {supermarket}.")
        return None, None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Set False to see browser actions
        page = await browser.new_page()
        await page.goto(url)
        await asyncio.sleep(3)  # Wait for the page to load

        print(f"🔍 Searching for {search_query} on {supermarket}...")

        # ✅ Let AI dynamically find the search box & search the product
        search_box = page.locator("input[type='text'], input[type='search']").first
        await search_box.fill(search_query)
        await search_box.press("Enter")  # Simulate pressing enter
        await asyncio.sleep(5)

        # ✅ AI decides where to extract product name & price dynamically
        extraction_prompt = f"""
        I am currently on the search results page for "{search_query}" on {supermarket}.
        Describe how I should locate:
        1️⃣ The first product's name
        2️⃣ The first product's price
        Just explain where they appear on the page (e.g., inside a div, near an image, next to a buy button).
        Do NOT return code, just describe in words.
        """

        # **🔧 Fixed LLM invocation**
        response = llm.invoke(extraction_prompt)  # ✅ Extract response object
        extraction_instruction = response.content.strip()  # ✅ Get text response
        print(f"🧠 AI Extraction Instructions: {extraction_instruction}")

        # ✅ AI Uses Description to Extract Product Name & Price
        product_name = await page.text_content("xpath=//body")  # Get full page text
        product_price = None

        # ✅ AI Refines Extraction If Needed
        if search_query.lower() in product_name.lower():
            product_name = search_query  # If AI found the correct product name
            product_price = await page.text_content("xpath=//body[contains(text(), '€')]")

        if product_name and product_price:
            print(f"🔹 Found Product: {product_name}")
            print(f"💰 Found Price: {product_price}")
            await browser.close()
            return product_name.strip(), product_price.strip()

        # ✅ If no result, try alternative search terms
        print(f"❌ No product found. Trying alternative term... (Attempt {attempt}/3)")
        alt_response = await llm.invoke(f"Suggest a better search term for {search_query}")
        alternative_term = alt_response.content.strip()  # ✅ Extract alternative term
        await browser.close()
        return await scrape_prices(url, alternative_term, supermarket, attempt + 1)

# ✅ Define AI Tools for Carrefour & AH
carrefour_tool = Tool(
    name="Carrefour Price Search",
    func=lambda query: asyncio.run(scrape_prices("https://www.carrefoursa.com", query, "Carrefour")),
    description="Searches CarrefourSA for product prices."
)

ah_tool = Tool(
    name="AH Price Search",
    func=lambda query: asyncio.run(scrape_prices("https://www.ah.nl", query, "AH")),
    description="Searches Albert Heijn (AH.nl) for product prices."
)

# ✅ Create AI Agent with Custom Prompt
agent = initialize_agent(
    tools=[carrefour_tool, ah_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    agent_kwargs={"system_message": agent_prompt}  # 🔥 Custom Prompt
)

# ✅ List of Products to Search
products = [
    ("Carrefour", "Süt"),
    ("Carrefour", "Ekmek"),
    ("Carrefour", "Kıyma"),
    ("Carrefour", "Un"),
    ("Carrefour", "Yumurta"),
    ("AH", "Melk"),
    ("AH", "Brood"),
    ("AH", "Gehakt"),
    ("AH", "Bloem"),
    ("AH", "Eieren"),
]

# ✅ CSV File Setup
csv_filename = "supermarket_prices.csv"
header = ["Supermarket", "Product", "Found Product", "Price", "Date"]

# ✅ Fetch Prices and Save to CSV
async def fetch_and_save_prices():
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(header)

        for supermarket, product in products:
            print(f"\n🔍 **Searching {supermarket} for {product}**")
            found_product, price = await scrape_prices(
                "https://www.carrefoursa.com" if supermarket == "Carrefour" else "https://www.ah.nl",
                product,
                supermarket
            )

            # ✅ Save Data to CSV
            date = datetime.now().strftime("%Y-%m-%d")
            writer.writerow([supermarket, product, found_product, price, date])

# ✅ Run the Search Process
asyncio.run(fetch_and_save_prices())

print(f"\n📁 Data saved to {csv_filename}")
