from flask import Flask, render_template
import csv

app = Flask(__name__)

def generate_static_html():
    with open("supermarket_prices.csv", newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        prices = list(reader)

    # ✅ Render template inside an application context
    with app.app_context():
        rendered_html = render_template("index.html", prices=prices)

        # ✅ Save static version to /docs
        with open("docs/index.html", "w", encoding="utf-8") as static_file:
            static_file.write(rendered_html)
    print("✅ Static HTML generated at docs/index.html")

@app.route("/")
def index():
    with open("supermarket_prices.csv", newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        prices = list(reader)

    return render_template("index.html", prices=prices)

if __name__ == "__main__":
    # Local development only
    app.run(debug=True)
