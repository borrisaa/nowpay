from flask import Flask, request, jsonify, redirect
import requests
import hmac
import hashlib

app = Flask(__name__)

# 你的配置（保持不变）
NOWPAYMENTS_API_KEY = "QBT21RV-SWQ4J79-KQNZD1P-QNSYH77"
NOWPAYMENTS_IPN_SECRET = "x9GiujGXpovf0c947GkQWrdgTon9Bxcr"

# 映射：payment_id → 你的订单号
payment_to_order = {}
# 已支付的业务订单号
paid_orders = set()

# --------------------------
# 统一支付入口：15 USDT 收款，纯 USDT 流程
# --------------------------
@app.route("/pay/<string:order_id>")
def create_payment(order_id):
    headers = {
        "x-api-key": NOWPAYMENTS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "price_amount": 15,       # ✅ 金额：15 USDT
        "price_currency": "usdt", # ✅ 计价货币：USDT
        "pay_currency": "usdt",   # ✅ 收款货币：USDT
        "order_id": order_id     # 你的 8 位订单号
    }
    resp = requests.post(
        "https://api.nowpayments.io/v1/payment",
        headers=headers,
        json=payload,
        timeout=20
    )
    data = resp.json()
    if resp.status_code in (200, 201):
        payment_id = data.get("payment_id")
        if payment_id:
            payment_to_order[payment_id] = order_id
            return redirect(f"https://nowpayments.io/payment/?iid={payment_id}")
    return f"Payment failed: {data.get('message', 'API error')}", 500

# --------------------------
# 回调接口（不变）
# --------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    raw_data = request.get_data()
    signature = request.headers.get("x-nowpayments-sig", "")
    calc_sig = hmac.new(NOWPAYMENTS_IPN_SECRET.encode(), raw_data, hashlib.sha512).hexdigest()
    if not hmac.compare_digest(calc_sig, signature):
        return "Invalid signature", 403
    data = request.get_json()
    payment_id = data.get("payment_id")
    status = data.get("payment_status")
    order_id = payment_to_order.get(payment_id)
    if order_id and status == "finished":
        paid_orders.add(order_id)
    return "OK"

# --------------------------
# 查询接口：用户输 8 位订单号
# --------------------------
@app.route("/check")
def check_order():
    order_id = request.args.get("orderId")
    return jsonify({"paid": order_id in paid_orders})

# --------------------------
# 健康检查
# --------------------------
@app.route("/health")
def health():
    return "running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
