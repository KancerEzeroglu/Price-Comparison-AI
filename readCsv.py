from flask import Flask, render_template
import csv

app = Flask(__name__)

@app.route("/")
def index():
    with open("supermarket_prices.csv", newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        prices = list(reader)

    rendered_html = render_template("index.html", prices=prices)

    # ✅ Save static version
    with open("docs/index.html", "w", encoding="utf-8") as static_file:
        static_file.write(rendered_html)

    return rendered_html

if __name__ == "__main__":
    app.run(debug=True)
