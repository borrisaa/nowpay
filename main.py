from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)
paid_orders = set()  # 存储已支付的订单号

# 1. 查询订单状态
@app.route("/check", methods=["GET"])
def check():
    order_id = request.args.get("orderId")
    if not order_id:
        return jsonify({"error": "orderId is required"}), 400
    return jsonify({"paid": order_id in paid_orders})

# 2. 接收 NowPayments 回调
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}
    order_id = data.get("order_id") or data.get("payment_id") or data.get("invoice_id")
    status = data.get("status") or data.get("payment_status")
    print(f"[{datetime.datetime.now()}] 回调结果: {status}, 订单: {order_id}")
    if status == "finished":
        paid_orders.add(order_id)
    return jsonify({"code": 0, "msg": "success"})

# 3. 健康检查
@app.route("/health", methods=["GET"])
def health():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
