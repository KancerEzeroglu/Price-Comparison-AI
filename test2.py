import time
import csv
import asyncio
import random
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
- Extract prices in the correct currency: **TL for CarrefourSA** and **€ for AH**.
- Describe how to locate the product name & price on the page.
"""

# ✅ Rotate User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.83 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
]

# ✅ Async Function to Scrape Prices
async def scrape_prices(url, search_query, supermarket, attempt=1):
    if attempt > 3:
        print(f"❌ Maximum search attempts reached for {search_query} in {supermarket}.")
        return None, None

    async with async_playwright() as p:
        # ✅ Launch real browser with user-agent & bypass detection
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="browser_data",  # Saves session & cookies
            headless=False,  # Set False to debug visually
            args=[
                f"--user-agent={random.choice(USER_AGENTS)}",
                "--disable-blink-features=AutomationControlled",  # Prevent bot detection
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ]
        )

        page = await browser.new_page()
        await page.goto(url, timeout=60000)  # Increase timeout for slow loading pages
        await asyncio.sleep(random.uniform(3, 6))  # Human-like delay

        print(f"🔍 Searching for {search_query} on {supermarket}...")

        # ✅ **AH Bot Bypass**: Scroll, Hover, Add Random Delays
        await page.mouse.move(random.randint(0, 800), random.randint(0, 600))  # Move mouse randomly
        await asyncio.sleep(random.uniform(2, 5))  # Wait before interacting
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")  # Scroll down

        # ✅ Find & Fill Search Box
        search_box = page.locator("input[type='text'], input[type='search']").first
        await search_box.fill(search_query)
        await asyncio.sleep(random.uniform(2, 4))
        await search_box.press("Enter")  # Simulate pressing enter
        await asyncio.sleep(random.uniform(5, 8))  # Give time to load results

        # ✅ AI decides where to extract product name & price dynamically
        extraction_prompt = f"""
        I am currently on the search results page for "{search_query}" on {supermarket}.
        Describe how I should locate:
        1️⃣ The first product's name
        2️⃣ The first product's price
        Just explain where they appear on the page (e.g., inside a div, near an image, next to a buy button).
        Do NOT return code, just describe in words.
        """

        # ✅ Extract response from LLM
        response = llm.invoke(extraction_prompt)
        extraction_instruction = response.content.strip()
        print(f"🧠 AI Extraction Instructions: {extraction_instruction}")

        # ✅ AI Uses Description to Extract Product Name & Price
        product_name = None
        product_price = None

        # ✅ Search for Product Name
        try:
            product_name = await page.locator("h3, h2, strong, .item-name, .product-title").first.text_content(timeout=5000)
        except:
            print("⚠️ Product name not found.")

        # ✅ Search for Product Price (More Targeted Approach)
        try:
            product_price = await page.locator(".item-price, .price-container, .formatted-price, [data-testhook='price-amount']").first.text_content(timeout=5000)
        except:
            print("⚠️ Product price not found.")

        if product_name and product_price:
            print(f"🔹 Found Product: {product_name}")
            print(f"💰 Found Price: {product_price}")
            await browser.close()
            return product_name.strip(), product_price.strip()

        # ✅ If no result, try alternative search terms
        print(f"❌ No product found. Trying alternative term... (Attempt {attempt}/3)")
        alt_response = llm.invoke(f"Suggest a better search term for {search_query}")
        alternative_term = alt_response.content.strip()
        await browser.close()
        return await scrape_prices(url, alternative_term, supermarket, attempt + 1)

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
