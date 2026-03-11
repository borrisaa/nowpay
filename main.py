from flask import Flask, request, jsonify, redirect
import requests
import hmac
import hashlib

app = Flask(__name__)

# 你的配置
NOWPAYMENTS_API_KEY = "QBT21RV-SWQ4J79-KQNZD1P-QNSYH77"
NOWPAYMENTS_IPN_SECRET = "x9GiujGXpovf0c947GkQWrdgTon9Bxcr"

# 映射：payment_id → 你的业务订单号
payment_to_order = {}
# 已支付的业务订单号
paid_orders = set()

# --------------------------
# 统一支付入口（用户点这个链接）
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
                # 关键：把 NowPayments 的 payment_id 和你的订单号绑定
                payment_to_order[payment_id] = order_id
                return redirect(f"https://nowpayments.io/payment/?iid={payment_id}")
        print(f"[Pay] {order_id} {resp.status_code} {resp.text}", flush=True)
    except Exception as e:
        print(f"[Pay] {order_id} {e}", flush=True)
    return "Payment failed", 500

# --------------------------
# 回调接口（NowPayments 调用）
# --------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        raw_data = request.get_data()
        signature = request.headers.get("x-nowpayments-sig", "")
        calc_sig = hmac.new(
            NOWPAYMENTS_IPN_SECRET.encode(),
            raw_data,
            hashlib.sha512
        ).hexdigest()
        if not hmac.compare_digest(calc_sig, signature):
            return "Invalid signature", 403

        data = request.get_json()
        payment_id = data.get("payment_id")
        status = data.get("payment_status")

        # 关键：通过 payment_id 找到你的订单号
        order_id = payment_to_order.get(payment_id)
        if order_id and status == "finished":
            paid_orders.add(order_id)
            print(f"[Webhook] 订单 {order_id} 支付成功", flush=True)
        return "OK"
    except Exception as e:
        print(f"[Webhook] {e}", flush=True)
        return "Error"

# --------------------------
# 用户查询：只需要输入自己的订单号！
# --------------------------
@app.route("/check")
def check_order():
    order_id = request.args.get("orderId")  # 用回 orderId，和你原来一致
    return jsonify({"paid": order_id in paid_orders})

# --------------------------
# 健康检查
# --------------------------
@app.route("/health")
def health():
    return "running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
