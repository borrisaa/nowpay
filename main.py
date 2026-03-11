from flask import Flask, request, jsonify, redirect
import datetime

app = Flask(__name__)

# 内存订单（重启清空，完全符合你要的简单模式）
paid_orders = set()

# 你自己在 NowPayments 后台生成的固定支付链接
FIXED_PAY_URL = "https://nowpayments.io/payment/?iid=5874033439"
FIXED_PAY_URL_BSC = "https://nowpayments.io/payment/?iid=5845644542"

# 新增：你的服务器回调地址（核心！自动回调全靠它）
CALLBACK_URL = "http://121.41.42.32:10000/webhook"

# ----------------------
# TRX 支付入口（已加 callback_url）
# ----------------------
@app.route("/pay/<int:order_id>", methods=["GET"])
def pay(order_id):
    order_id_str = str(order_id)
    # 关键：拼接 callback_url，让 NowPayments 自动发回调
    pay_url = f"{FIXED_PAY_URL}&orderId={order_id_str}&callback_url={CALLBACK_URL}"
    return redirect(pay_url)

# ----------------------
# BSC 支付入口（已加 callback_url）
# ----------------------
@app.route("/pay_bsc/<int:order_id>", methods=["GET"])
def pay_bsc(order_id):
    order_id_str = str(order_id)
    pay_url = f"{FIXED_PAY_URL_BSC}&orderId={order_id_str}&callback_url={CALLBACK_URL}"
    return redirect(pay_url)

# ----------------------
# NowPayments 回调（完全不变，兼容你现有逻辑）
# ----------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}
    print(f"[{datetime.datetime.now()}] 收到回调:", data)

    order_id = data.get("order_id") or data.get("payment_id") or data.get("invoice_id")
    status = data.get("status") or data.get("payment_status")

    if order_id and status in ["confirmed", "finished", "success"]:
        paid_orders.add(str(order_id))
        print(f"[{datetime.datetime.now()}] 订单 {order_id} 已付款")

    return "ok", 200

# ----------------------
# 查询是否付款（完全不变）
# ----------------------
@app.route("/check", methods=["GET"])
def check():
    order_id = request.args.get("orderId")
    is_paid = order_id in paid_orders
    return jsonify({"paid": is_paid})

# ----------------------
# 销毁订单（激活后用，完全不变）
# ----------------------
@app.route("/consume", methods=["GET"])
def consume():
    order_id = request.args.get("orderId")
    if order_id in paid_orders:
        paid_orders.remove(order_id)
    return jsonify({"ok": True})

# ----------------------
# 健康检查（完全不变）
# ----------------------
@app.route("/health", methods=["GET"])
def health():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
