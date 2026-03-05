from flask import Flask, request, jsonify
import uuid
import threading
import time
import requests

app = Flask(__name__)

# 内存记录已付款订单（重启清空，符合你不记人、不留痕逻辑）
paid_orders = set()

# 你的固定收款链接
FIXED_PAYMENT_URL = "https://nowpayments.io/payment/?iid=5874033439"

# ----------------------
# 1. 用户激活 → 生成临时订单，跳固定支付链接
# ----------------------
@app.route("/activate", methods=["GET"])
def activate():
    # 生成一次性订单号（不记录用户身份，只记订单）
    order_id = "order_" + str(uuid.uuid4())
    # 拼接：固定支付链接 + 带上订单号
    pay_url = f"{FIXED_PAYMENT_URL}&orderId={order_id}"
    return jsonify({
        "orderId": order_id,
        "payUrl": pay_url
    })

# ----------------------
# 2. NowPayments 回调通知 → 标记订单已付款
# ----------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    order_id = data.get("orderId")
    status = data.get("paymentStatus")  # 一般是 success / failed

    if status == "success" and order_id:
        paid_orders.add(order_id)  # 只标记订单，不记录人
    return "ok", 200

# ----------------------
# 3. 机器人验证：这个订单有没有付过？
# ----------------------
@app.route("/check", methods=["GET"])
def check():
    order_id = request.args.get("orderId")
    paid = order_id in paid_orders
    return jsonify({"paid": paid})

# ----------------------
# 4. 机器人服务完成后，删除订单（一次一用）
# ----------------------
@app.route("/consume", methods=["GET"])
def consume():
    order_id = request.args.get("orderId")
    if order_id in paid_orders:
        paid_orders.remove(order_id)
    return jsonify({"ok": True})

# ----------------------
# 5. 防休眠：自己访问自己，永不休眠
# ----------------------
def keep_awake():
    while True:
        try:
            # 访问自己的轻量路由，防止休眠
            requests.get("https://nowpayments-callback.onrender.com/health", timeout=15)
        except:
            pass
        time.sleep(60 * 3)  # 每3分钟访问一次

@app.route("/health", methods=["GET"])
def health():
    return "ok", 200

# 启动防休眠线程
threading.Thread(target=keep_awake, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
