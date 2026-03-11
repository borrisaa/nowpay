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
# NowPayments 回调（核心：优先取 payment_id，这是唯一 100% 能拿到的字段）
# ----------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}
    print(f"[{datetime.datetime.now()}] 收到完整回调数据:", data) # 打印完整数据，方便调试

    # 🔥 核心逻辑：优先取 NowPayments 自己的 payment_id（这是唯一 100% 能拿到的字段）
    order_id = (
        data.get("payment_id") 
        or data.get("orderId")
        or data.get("order_id")
        or data.get("id")
        or data.get("invoice_id")
        or str(data.get("payment"))
        or data.get("metadata", {}).get("order_id")
    )
    
    # 🔥 识别所有可能的成功状态
    status = data.get("status") or data.get("payment_status")

    print(f"识别到的订单号: {order_id}, 状态: {status}")

    # 如果有订单号且状态是成功/完成
    if order_id and status in ["confirmed", "finished", "success", "completed", "paid"]:
        paid_orders.add(str(order_id))
        print(f"[{datetime.datetime.now()}] ✅ 订单 {order_id} 已成功标记为已付款！")

    return "ok", 200

# ----------------------
# 查询支付状态（修复类型匹配问题）
# ----------------------
@app.route("/check", methods=["GET"])
def check():
    order_id = request.args.get("orderId") or request.args.get("order_id")
    is_paid = str(order_id) in paid_orders # 强制转成字符串，避免类型不匹配
    return jsonify({"paid": is_paid})

# ----------------------
# 激活后销毁订单
# ----------------------
@app.route("/consume", methods=["GET"])
def consume():
    order_id = request.args.get("orderId") or request.args.get("order_id")
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
    app.run(host="0.0.0.0", port=10000, debug=False)
