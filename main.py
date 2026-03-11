from flask import Flask, request, jsonify, redirect
import requests
import hmac
import hashlib

app = Flask(__name__)

# 你的配置（不变）
NOWPAYMENTS_API_KEY = "QBT21RV-SWQ4J79-KQNZD1P-QNSYH77"
NOWPAYMENTS_IPN_SECRET = "x9GiujGXpovf0c947GkQWrdgTon9Bxcr"

# 存储已支付的 payment_id（和用户看到的 Payment ID 完全一致）
paid_payments = set()

# --------------------------
# 1. TRC20 USDT 支付入口（从日志验证可用）
# --------------------------
@app.route("/pay_trx/<string:order_id>")
def pay_trx(order_id):
    headers = {
        "x-api-key": NOWPAYMENTS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "price_amount": 15,
        "price_currency": "usd",
        "pay_currency": "usdttrc20",  # 必须传，日志里验证过
        "order_id": order_id
    }
    try:
        resp = requests.post(
            "https://api.nowpayments.io/v1/payment",
            headers=headers,
            json=payload,
            timeout=15
        )
        data = resp.json()
        if resp.status_code in (200, 201):
            payment_id = data.get("payment_id")
            if payment_id:
                return redirect(f"https://nowpayments.io/payment/?iid={payment_id}")
        print(f"[TRX] {order_id} {resp.status_code} {resp.text}", flush=True)
    except Exception as e:
        print(f"[TRX] {order_id} {e}", flush=True)
    return "Payment failed", 500

# --------------------------
# 2. BSC USDT 支付入口（从日志验证可用）
# --------------------------
@app.route("/pay_bsc/<string:order_id>")
def pay_bsc(order_id):
    headers = {
        "x-api-key": NOWPAYMENTS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "price_amount": 15,
        "price_currency": "usd",
        "pay_currency": "usdtbsc",  # 必须传，日志里验证过
        "order_id": order_id
    }
    try:
        resp = requests.post(
            "https://api.nowpayments.io/v1/payment",
            headers=headers,
            json=payload,
            timeout=15
        )
        data = resp.json()
        if resp.status_code in (200, 201):
            payment_id = data.get("payment_id")
            if payment_id:
                return redirect(f"https://nowpayments.io/payment/?iid={payment_id}")
        print(f"[BSC] {order_id} {resp.status_code} {resp.text}", flush=True)
    except Exception as e:
        print(f"[BSC] {order_id} {e}", flush=True)
    return "Payment failed", 500

# --------------------------
# 3. 回调接口（和你后台 Webhook 地址一致）
# --------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        raw_data = request.get_data()
        signature = request.headers.get("x-nowpayments-sig", "")

        # 验签（和你之前手动回调逻辑一致）
        calc_sig = hmac.new(
            NOWPAYMENTS_IPN_SECRET.encode(),
            raw_data,
            hashlib.sha512
        ).hexdigest()
        if not hmac.compare_digest(calc_sig, signature):
            return "Invalid signature", 403

        data = request.get_json()
        payment_id = data.get("payment_id")  # 从你历史回调验证的字段
        status = data.get("payment_status")

        if payment_id and status == "finished":
            paid_payments.add(payment_id)
            print(f"[Webhook] Payment {payment_id} paid", flush=True)

        return "OK", 200
    except Exception as e:
        print(f"[Webhook] {e}", flush=True)
        return "Error", 500

# --------------------------
# 4. 用户查询：输入他看到的 Payment ID
# --------------------------
@app.route("/check")
def check():
    payment_id = request.args.get("paymentId")
    return jsonify({"paid": payment_id in paid_payments})

# --------------------------
# 健康检查
# --------------------------
@app.route("/health")
def health():
    return "running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
