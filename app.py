from flask import Flask, request, jsonify
import requests
import pandas as pd
from datetime import datetime, timedelta

app = Flask(__name__)

# كاش لتخزين سعر الصرف
exchange_cache = {
    "timestamp": None,
    "rates": {}
}
# دالة لجلب سعر الصرف من الإنترنت
def get_exchange_rates():
    now = datetime.now()
    if exchange_cache["timestamp"] is None or (now - exchange_cache["timestamp"]) > timedelta(hours=1):
        response = requests.get("https://api.exchangerate-api.com/v4/latest/MAD")
        if response.status_code == 200:
            data = response.json()
            rates = {
                "USD": data["rates"].get("USD"),
                "AED": data["rates"].get("AED")
            }
            exchange_cache["timestamp"] = now
            exchange_cache["rates"] = rates
        else:
            raise Exception("Failed to fetch exchange rates.")
    return exchange_cache["rates"]

# API: تحويل مبلغ واحد
@app.route('/convert', methods=['POST'])
def convert_amount():
    data = request.get_json()
    amount = float(data.get("amount", 0))
    rates = get_exchange_rates()
    result = {
        "amount_MAD": amount,
        "amount_USD": round(amount * rates["USD"], 2),
        "amount_AED": round(amount * rates["AED"], 2),
        "timestamp": exchange_cache["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    }
    return jsonify(result)

# API: رفع ملف إكسل وتحويل جميع المبالغ
@app.route('/upload', methods=['POST'])
def upload_excel():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided"}), 400
    
    df = pd.read_excel(file)
    if "Montant Colis" not in df.columns:
        return jsonify({"error": "Column 'Montant Colis' not found in Excel"}), 400

    rates = get_exchange_rates()
    df["USD"] = df["Montant Colis"] * rates["USD"]
    df["AED"] = df["Montant Colis"] * rates["AED"]
    summary = {
        "total_MAD": round(df["Montant Colis"].sum(), 2),
        "total_USD": round(df["USD"].sum(), 2),
        "total_AED": round(df["AED"].sum(), 2)
    }
    return jsonify(summary)

from flask import render_template

@app.route('/')
def index():
    return render_template('interface.html')

if __name__ == '__main__':
    app.run(debug=True)
