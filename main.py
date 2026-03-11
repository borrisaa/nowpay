from flask import Flask, request, jsonify, redirect
import datetime

app = Flask(__name__)

# 内存订单（重启清空，简单模式）
paid_orders = set()

# 你自己的 NowPayments 固定支付链接（保持不变）
FIXED_PAY_URL = "https://nowpayments.io/payment/?iid=5874033439"
FIXED_PAY_URL_BSC = "https://nowpayments.io/payment/?iid=5845644542"

# 服务器回调地址（核心，自动回调）
CALLBACK_URL = "http://121.41.42.32:10000/webhook"

# ----------------------
# TRX 支付入口
# ----------------------
@app.route("/pay/<int:order_id>", methods=["GET"])
def pay(order_id):
    order_id_str = str(order_id)
    pay_url = f"{FIXED_PAY_URL}&orderId={order_id_str}&callback_url={CALLBACK_URL}"
    return redirect(pay_url)

# ----------------------
# BSC 支付入口
# ----------------------
@app.route("/pay_bsc/<int:order_id>", methods=["GET"])
def pay_bsc(order_id):
    order_id_str = str(order_id)
    pay_url = f"{FIXED_PAY_URL_BSC}&orderId={order_id_str}&callback_url={CALLBACK_URL}"
    return redirect(pay_url)

# ----------------------
# NowPayments 回调（已兼容所有字段名）
# ----------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}
    print(f"[{datetime.datetime.now()}] 收到回调:", data)

    # 兼容 NowPayments 所有可能的订单号字段名
    order_id = (
        data.get("order_id") 
        or data.get("orderId")
        or data.get("payment_id") 
        or data.get("invoice_id")
        or data.get("metadata", {}).get("order_id")
    )
    status = data.get("status") or data.get("payment_status")

    if order_id and status in ["confirmed", "finished", "success"]:
        paid_orders.add(str(order_id))
        print(f"[{datetime.datetime.now()}] 订单 {order_id} 已付款")

    return "ok", 200

# ----------------------
# 查询支付状态
# ----------------------
@app.route("/check", methods=["GET"])
def check():
    order_id = request.args.get("orderId")
    is_paid = order_id in paid_orders
    return jsonify({"paid": is_paid})

# ----------------------
# 激活后销毁订单
# ----------------------
@app.route("/consume", methods=["GET"])
def consume():
    order_id = request.args.get("orderId")
    if order_id in paid_orders:
        paid_orders.remove(order_id)
    return jsonify({"ok": True})

# ----------------------
# 健康检查
# ----------------------
@app.route("/health", methods=["GET"])
def health():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
