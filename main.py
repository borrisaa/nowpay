from flask import Flask, request, jsonify, redirect
import datetime
import hmac
import hashlib
import requests

app = Flask(__name__)

# 内存状态
paid_orders = set()
order_to_payment = {}

# 你真实的密钥
NOWPAYMENTS_API_KEY = "QBT21RV-SWQ4J79-KQNZD1P-QNSYH77"
NOWPAYMENTS_IPN_SECRET = "x9GiujGXpovf0c947GkQWrdgTon9Bxcr"
CALLBACK_URL = "http://121.41.42.32:10000/webhook"

# ----------------------
# TRX 支付（15 USDT）
# ----------------------
@app.route("/pay/<int:order_id>", methods=["GET"])
def pay(order_id):
    order_id_str = str(order_id)
    headers = {
        "x-api-key": NOWPAYMENTS_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "price_amount": 15,
        "price_currency": "usd",
        "pay_currency": "trx",
        "order_id": order_id_str,
        "callback_url": CALLBACK_URL
    }
    try:
        resp = requests.post("https://api.nowpayments.io/v1/payment", headers=headers, json=data, timeout=10)
        if resp.status_code in (200, 201):
            pay_url = resp.json()["payment_url"]
            order_to_payment[order_id_str] = None
            return redirect(pay_url)
    except Exception as e:
        print(f"TRX 错误: {e}", flush=True)
    return "支付链接创建失败", 500

# ----------------------
# BSC 支付（15 USDT）
# ----------------------
@app.route("/pay_bsc/<int:order_id>", methods=["GET"])
def pay_bsc(order_id):
    order_id_str = str(order_id)
    headers = {
        "x-api-key": NOWPAYMENTS_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "price_amount": 15,
        "price_currency": "usd",
        "pay_currency": "bnb",
        "order_id": order_id_str,
        "callback_url": CALLBACK_URL
    }
    try:
        resp = requests.post("https://api.nowpayments.io/v1/payment", headers=headers, json=data, timeout=10)
        if resp.status_code in (200, 201):
            pay_url = resp.json()["payment_url"]
            order_to_payment[order_id_str] = None
            return redirect(pay_url)
    except Exception as e:
        print(f"BSC 错误: {e}", flush=True)
    return "支付链接创建失败", 500

# ----------------------
# IPN 回调（和你之前一样）
# ----------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    raw_data = request.get_data()
    signature = request.headers.get("X-NowPayments-Signature", "")
    computed_hmac = hmac.new(
        NOWPAYMENTS_IPN_SECRET.encode("utf-8"),
        raw_data,
        hashlib.sha512
    ).hexdigest()

    data = request.get_json(silent=True) or {}
    payment_id = str(data.get("payment_id") or data.get("payment", {}).get("id") or "")
    client_order_id = data.get("order_id") or ""
    status = data.get("status") or data.get("payment_status") or ""

    if client_order_id and payment_id:
        order_to_payment[str(client_order_id)] = payment_id
    if payment_id and status in ["finished", "confirmed", "success", "paid", "completed"]:
        paid_orders.add(payment_id)
    return "ok"

# ----------------------
# 机器人查询接口（完全不变）
# ----------------------
@app.route("/check", methods=["GET"])
def check():
    order_id = request.args.get("orderId") or ""
    if not order_id:
        return jsonify({"paid": False})
    pid = order_to_payment.get(str(order_id))
    return jsonify({"paid": pid in paid_orders})

# ----------------------
# 健康检查
# ----------------------
@app.route("/health")
def health():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
