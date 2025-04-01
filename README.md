# 🛒 Supermarket Price Comparison with AI

This project compares grocery prices between Turkish and Dutch supermarkets using AI, web scraping, and a simple web interface.

🌐 **Live Demo**: [https://price-comparison-ai.onrender.com/](https://price-comparison-ai.onrender.com/)

---

## 🚀 What It Does

- Searches product prices on **CarrefourSA (Turkey)** and **Albert Heijn (Netherlands)**
- Uses **Playwright** to simulate human browsing and avoid bot detection
- Extracts:
  - ✅ Product Name
  - 💰 Price
  - 📦 Quantity (e.g., 1 kg, 6 eggs)
  - 📅 Date
- Uses **Gemini (Google AI)** to intelligently handle:
  - Page analysis
  - Quantity parsing
  - Better search term suggestions if no results are found
- Displays the results in a clean **HTML table** using a Flask web app

---

## 🧰 Technologies Used

- Python 3.10+
- [Flask](https://flask.palletsprojects.com/)
- [Playwright (Async)](https://playwright.dev/python/)
- [Google Gemini API](https://ai.google.dev/)
- HTML + CSS (for web UI)

---

## ⚙️ How to Run It Locally

### 1. 📦 Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. 🔑 Set Your Gemini API Key
Update your API key in priceComparison.py:

```bash
google_api_key = "YOUR_GEMINI_API_KEY"
```

### 3. 📦 Scrape Prices

```bash
python3 priceComparison.py
```

This will create a CSV file like: `supermarket_prices.csv`

### 4. 🌐 Launch the Flask App

```bash
python3 readCsv.py
```

Then open your browser at: http://127.0.0.1:5000

### 🔐 Notes on Bot Detection
To avoid getting blocked:
- Random user-agent rotation
- Simulated mouse, keyboard, scroll behavior
- Launches Playwright in persistent session mode
- Masks common bot signatures (e.g., navigator.webdriver)

Note: Albert Heijn may still block access — use proxy/VPN if needed.

## ☁️ Deployment
✅ The app is deployed live at:
https://price-comparison-ai.onrender.com/

You can use Render or similar platforms to host it for free.

## 📈 Future Features
- Historical price trend tracking
- Multi-country support
- Visual charts for price comparison
- JSON API for external use
- Cron job for automatic scraping

## 📄 License
Licensed under the MIT License — you're free to use, modify, and distribute it. Just don’t abuse third-party websites or scrape them too aggressively.

Happy scraping! 🛒
