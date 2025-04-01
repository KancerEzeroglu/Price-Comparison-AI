from flask import Flask, render_template
import csv

app = Flask(__name__)

def read_csv():
    data = []
    with open('supermarket_prices.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)
    return data

@app.route('/')
def index():
    prices = read_csv()
    return render_template('index.html', prices=prices)

if __name__ == '__main__':
    app.run(debug=True)
