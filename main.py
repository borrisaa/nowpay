from flask import Flask, request, jsonify, redirect
import hmac
import hashlib
import requests

app = Flask(__name__)

paid_orders = set()
order_map = {}

NOWPAYMENTS_API_KEY = "QBT21RV-SWQ4J79-KQNZD1P-QNSYH79"
NOWPAYMENTS_IPN_SECRET = "x9GiujGXpovf0c947GkQWrdgTon9Bxcr"

# 统一支付入口（用户只需要这一个链接，内部自动支持 BSC + TRX）
@app.route("/pay/<int:order_id>", methods=["GET"])
def create_payment(order_id):
    order_id_str = str(order_id)
    headers = {
        "x-api-key": NOWPAYMENTS_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "price_amount": 15,
        "price_currency": "usd",
        "pay_currency": "usdtbsc",
        "order_id": order_id_str
    }
    try:
        resp = requests.post("https://api.nowpayments.io/v1/payment", headers=headers, json=data, timeout=15)
        if resp.status_code in (200, 201):
            res = resp.json()
            purchase_id = res.get("purchase_id")
            order_map[order_id_str] = res
            return redirect(f"https://nowpayments.io/payment/?iid={purchase_id}")
    except Exception as e:
        print(f"[ERROR] {e}", flush=True)
    return "Payment link failed", 500

# 回调地址（NowPayments 后台填写：http://你的IP:10000/ipn）
@app.route("/ipn", methods=["POST"])
def ipn_handler():
    try:
        data = request.get_json()
        order_id = data.get("order_id")
        status = data.get("payment_status")
        if status == "finished" and order_id:
            paid_orders.add(order_id)
        return "OK", 200
    except:
        return "ERR", 400

# 查询订单是否支付（给机器人调用）
@app.route("/check", methods=["GET"])
def check_order():
    order_id = request.args.get("orderId")
    return jsonify({"paid": order_id in paid_orders})

# 健康检查
@app.route("/health")
def health():
    return "running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
