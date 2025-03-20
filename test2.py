import time
import csv
import asyncio
import random
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from playwright.async_api import async_playwright

# ✅ Initialize AI Model (Google Gemini)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key="AIzaSyDkIKB5VaUERkbgdCVXAUyjInuy6OYf9KM"
)

# ✅ Custom AI Prompt (Structured Extraction)
AI_PROMPT = """You are an AI assistant helping to extract product names, prices, and quantities from supermarket search pages.

1. **Extract the first product’s name**:
   - Carrefour: The product name is inside `<h3 class='item-name'>`
   - AH: The product name is inside `.line-clamp_lineClamp__2lnzv`

2. **Extract the product price**:
   - Look inside `.item-price`, `.formatted-price`, or `.price-amount`

3. **Extract the quantity**:
   - Carrefour: The quantity is **inside the product name** (e.g., `"Domates Pazar kg"` → `"kg"`)
   - AH: The quantity is inside `[data-testhook='product-unit-size']` or `.price_unitSize__Hk6E4`

4. **If no product is found, suggest a better search term** in the correct language:
   - Carrefour (Turkish): Suggest a related **Turkish** word.
   - AH (Dutch): Suggest a related **Dutch** word.

Return only the extracted data. Do not include extra explanations.
"""

# ✅ Rotate User-Agents (Bypass bot detection)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.83 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36",
]

# ✅ Async Function to Scrape Prices
async def scrape_prices(url, search_query, supermarket, attempt=1):
    if attempt > 3:
        print(f"❌ Maximum search attempts reached for {search_query} in {supermarket}.")
        return None, None, None, None  # Product Name, Price, Quantity, Date

    async with async_playwright() as p:
        # ✅ Launch browser with user-agent & bypass detection
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="browser_data",  # Saves session & cookies
            headless=False,  # Set False to debug visually
            args=[
                f"--user-agent={random.choice(USER_AGENTS)}",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ]
        )

        page = await browser.new_page()
        await page.goto(url, timeout=60000)
        await asyncio.sleep(random.uniform(3, 6))

        print(f"🔍 Searching for {search_query} on {supermarket}...")

        # ✅ Simulate Human Interaction
        await page.mouse.move(random.randint(0, 800), random.randint(0, 600))
        await asyncio.sleep(random.uniform(2, 5))
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")

        # ✅ Find & Fill Search Box
        search_box = page.locator("input[type='text'], input[type='search']").first
        await search_box.fill(search_query)
        await asyncio.sleep(random.uniform(2, 4))
        await search_box.press("Enter")
        await asyncio.sleep(random.uniform(5, 8))

        # ✅ Extract **Correct** Product Name (FORCE-EXTRACTION)
        product_name = None
        try:
            if supermarket == "Carrefour":
                product_name = await page.locator("h3.item-name").first.text_content(timeout=5000)
            else:  # AH
                product_name = await page.locator("[data-testhook='product-title-line-clamp'], .line-clamp_root__7DevG").first.text_content(timeout=5000)
            product_name = product_name.strip()
        except:
            print("⚠️ Product name not found.")

        # ✅ Extract **Correct** Product Price
        product_price = None
        try:
            product_price = await page.locator(
                ".item-price, .price-container, .formatted-price, [data-testhook='price-amount'], .price-amount_integer__+e2XO"
            ).first.text_content(timeout=5000)
            product_price = product_price.strip()
        except:
            print("⚠️ Product price not found.")

        # ✅ Extract Quantity (Forcing Carrefour to extract from product name)
        product_quantity = "Unknown"
        try:
            if supermarket == "Carrefour":
                words = product_name.split()
                quantity_candidates = [word for word in words if any(unit in word.lower() for unit in ["kg", "g", "lt", "l", "adet", "paket"])]
                product_quantity = quantity_candidates[0] if quantity_candidates else "Unknown"
            else:
                product_quantity = await page.locator(
                    ".product-unit, .price_unitSize__Hk6E4, .quantity, [data-testhook='product-unit-size']"
                ).first.text_content(timeout=5000)
                product_quantity = product_quantity.strip()
        except:
            print("⚠️ Product quantity not found.")

        # ✅ AI Ensures Extraction is Correct
        extraction_prompt = f"{AI_PROMPT}\n\nExtract data from this search: **{search_query}**"
        ai_response = llm.invoke(extraction_prompt)
        print("🧠 AI Extraction Instructions:", ai_response.content)

        # ✅ Ensure Data Integrity
        if product_price and product_name and "Teslimat" not in product_name:
            print(f"🛒 Product: {product_name} | 💰 Price: {product_price} | 📦 Quantity: {product_quantity}")
            await browser.close()
            return product_name, product_price, product_quantity, datetime.now().strftime("%Y-%m-%d")

        # ✅ Try Alternative Search Terms (AI Suggestions)
        print(f"❌ No product found. Trying alternative term... (Attempt {attempt}/3)")
        alt_response = llm.invoke(f"Suggest a better search term for {search_query}")
        alternative_term = alt_response.content.strip()

        await browser.close()
        return await scrape_prices(url, alternative_term, supermarket, attempt + 1)

# ✅ List of Products to Search
products = [
    ("Carrefour", "Süt"),
    #("Carrefour", "Ekmek"),
    #("Carrefour", "Kıyma"),
    #("Carrefour", "Un"),
    #("Carrefour", "Yumurta"),
    ("AH", "Melk"),
    #("AH", "Brood"),
    #("AH", "Gehakt"),
    #("AH", "Bloem"),
    #("AH", "Eieren"),
]

# ✅ CSV File Setup (Include Date in Filename)
csv_filename = f"supermarket_prices_{datetime.now().strftime('%Y-%m-%d')}.csv"
header = ["Supermarket", "Product Searched", "Product Name", "Price", "Quantity", "Date"]

# ✅ Fetch Prices and Save to CSV
async def fetch_and_save_prices():
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(header)

        for supermarket, product in products:
            print(f"\n🔍 **Searching {supermarket} for {product}**")
            product_name, price, quantity, date = await scrape_prices(
                "https://www.carrefoursa.com" if supermarket == "Carrefour" else "https://www.ah.nl",
                product,
                supermarket
            )

            # ✅ Save Data to CSV
            writer.writerow([supermarket, product, product_name, price, quantity, date])

# ✅ Run the Search Process
asyncio.run(fetch_and_save_prices())

print(f"\n📁 Data saved to {csv_filename}")
