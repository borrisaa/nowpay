from flask import Flask, request, jsonify, redirect

app = Flask(__name__)

# 内存中存储已付款订单（重启后清空，不影响单次使用）
paid_orders = set()

# 你的固定收款链接
FIXED_PAY_URL = "https://nowpayments.io/payment/?iid=5874033439"
# 新增：BSC 链固定收款链接
FIXED_PAY_URL_BSC = "https://nowpayments.io/payment/?iid=5845644542"

# ----------------------
# 1. 激活/生成订单（兼容旧版 /pay/8位数字）
# ----------------------
@app.route("/pay/<int:order_id>", methods=["GET"])
def pay(order_id):
    order_id_str = str(order_id)
    # 把订单号拼到固定收款链接上，生成最终支付链接
    pay_url = f"{FIXED_PAY_URL}&orderId={order_id_str}"
    # 直接跳转到支付页，不再返回JSON
    return redirect(pay_url)

# ----------------------
# 新增：BSC 链支付路由（结构和 TRX 完全一样）
# ----------------------
@app.route("/pay_bsc/<int:order_id>", methods=["GET"])
def pay_bsc(order_id):
    order_id_str = str(order_id)
    pay_url = f"{FIXED_PAY_URL_BSC}&orderId={order_id_str}"
    return redirect(pay_url)

# ----------------------
# 2. NowPayments 回调：标记订单已付款
# ----------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}
    order_id = data.get("orderId")
    status = data.get("paymentStatus")

    if order_id and status == "success":
        paid_orders.add(order_id)

    return "ok"

# ----------------------
# 3. 检查订单是否已付款
# ----------------------
@app.route("/check", methods=["GET"])
def check():
    order_id = request.args.get("orderId")
    return jsonify({
        "paid": order_id in paid_orders
    })

# ----------------------
# 4. 用完一次就销毁订单
# ----------------------
@app.route("/consume", methods=["GET"])
def consume():
    order_id = request.args.get("orderId")
    if order_id in paid_orders:
        paid_orders.remove(order_id)
    return jsonify({"ok": True})

# ----------------------
# 5. 健康检查：防止 Render 休眠
# ----------------------
@app.route("/health", methods=["GET"])
def health():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
