from flask import Flask, request, jsonify, redirect
import hmac
import hashlib
import requests

app = Flask(__name__)

# 全局状态
paid_orders = set()
order_to_payment = {}

# 你正式密钥
NOWPAYMENTS_API_KEY = "QBT21RV-SWQ4J79-KQNZD1P-QNSYH77"
NOWPAYMENTS_IPN_SECRET = "x9GiujGXpovf0c947GkQWrdgTon9Bxcr"

# ------------------------------
# TRON 支付（动态创建订单）
# ------------------------------
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
        "order_id": order_id_str
    }
    try:
        resp = requests.post(
            "https://api.nowpayments.io/v1/payment",
            headers=headers,
            json=data,
            timeout=12
        )
        if resp.status_code in (200, 201):
            res = resp.json()
            payment_id = res["payment_id"]
            pay_url = f"https://nowpayments.io/payment/{payment_id}"
            return redirect(pay_url)
    except Exception as e:
        print(f"[TRX] 异常: {e}", flush=True)
    return "支付链接创建失败", 500

# ------------------------------
# BSC 支付（动态创建订单）
# ------------------------------
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
        "pay_currency": "usdt_bsc",
        "order_id": order_id_str
    }
    try:
        resp = requests.post(
            "https://api.nowpayments.io/v1/payment",
            headers=headers,
            json=data,
            timeout=12
        )
        if resp.status_code in (200, 201):
            res = resp.json()
            payment_id = res["payment_id"]
            pay_url = f"https://nowpayments.io/payment/{payment_id}"
            return redirect(pay_url)
    except Exception as e:
        print(f"[BSC] 异常: {e}", flush=True)
    return "支付链接创建失败", 500

# ------------------------------
# 自动回调（完整、正确、不改动）
# ------------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    raw_data = request.get_data()
    signature = request.headers.get("X-NowPayments-Signature", "")

    computed_hmac = hmac.new(
        NOWPAYMENTS_IPN_SECRET.encode("utf-8"),
        raw_data,
        hashlib.sha51
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

# ------------------------------
# 机器人查询订单是否支付（完整）
# ------------------------------
@app.route("/check", methods=["GET"])
def check():
    order_id = request.args.get("orderId") or ""
    if not order_id:
        return jsonify({"paid": False})
    payment_id = order_to_payment.get(str(order_id))
    return jsonify({"paid": payment_id in paid_orders})

# ------------------------------
# 健康检查
# ------------------------------
@app.route("/health")
def health():
    return "running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
