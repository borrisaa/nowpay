from flask import Flask, request, jsonify, redirect
import requests
import hmac
import hashlib

app = Flask(__name__)

# 你的配置
NOWPAYMENTS_API_KEY = "QBT21RV-SWQ4J79-KQNZD1P-QNSYH77"
NOWPAYMENTS_IPN_SECRET = "x9GiujGXpovf0c947GkQWrdgTon9Bxcr"

# 已支付的 payment_id（和用户看到的 Payment ID 一致）
paid_payments = set()

# --------------------------
# 统一支付入口（机器人只需要这一个）
# --------------------------
@app.route("/pay/<string:order_id>")
def create_payment(order_id):
    headers = {
        "x-api-key": NOWPAYMENTS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "price_amount": 15,
        "price_currency": "usd",
        "order_id": order_id,
        # 只允许所有 USDT 通道，用户打开后自己选
        "allowed_coins": ["usdttrc20", "usdtbsc", "usdteth", "usdtarb", "usdtopt"]
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
        print(f"[Pay] {order_id} {resp.status_code} {resp.text}", flush=True)
    except Exception as e:
        print(f"[Pay] {order_id} {e}", flush=True)
    return "Payment failed", 500

# --------------------------
# 回调接口（和后台 Webhook 一致）
# --------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        raw_data = request.get_data()
        signature = request.headers.get("x-nowpayments-sig", "")
        calc_sig = hmac.new(NOWPAYMENTS_IPN_SECRET.encode(), raw_data, hashlib.sha512).hexdigest()
        if not hmac.compare_digest(calc_sig, signature):
            return "Invalid signature", 403

        data = request.get_json()
        payment_id = data.get("payment_id")
        status = data.get("payment_status")
        if payment_id and status == "finished":
            paid_payments.add(payment_id)
            print(f"[Webhook] Payment {payment_id} paid", flush=True)
        return "OK"
    except Exception as e:
        print(f"[Webhook] {e}", flush=True)
        return "Error"

# --------------------------
# 用户查询：输入 Payment ID
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
