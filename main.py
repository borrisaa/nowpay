from flask import Flask, request, jsonify, redirect

app = Flask(__name__)

paid_orders = set()

# TRON链静态收款链接（确保这里是 TRON 的 iid）
FIXED_PAY_URL_TRON = "https://nowpayments.io/payment/?iid=5874033439"
# BSC链静态收款链接（确保这里是 BSC 的 iid）
FIXED_PAY_URL_BSC = "https://nowpayments.io/payment/?iid=4868011124"

# TRON链支付路由
@app.route("/pay/<int:order_id>")
def pay(order_id):
    order_id_str = str(order_id)
    pay_url = f"{FIXED_PAY_URL_TRON}&orderId={order_id_str}"
    return redirect(pay_url)

# BSC链支付路由
@app.route("/pay_bsc/<int:order_id>")
def pay_bsc(order_id):
    order_id_str = str(order_id)
    pay_url = f"{FIXED_PAY_URL_BSC}&orderId={order_id_str}"
    return redirect(pay_url)

# 收款回调接口
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}
    order_id = data.get("orderId")
    status = data.get("paymentStatus")
    if order_id and status == "success":
        paid_orders.add(order_id)
    return "ok"

# 订单付款检查接口
@app.route("/check")
def check():
    order_id = request.args.get("orderId")
    return jsonify({"paid": order_id in paid_orders})

# 订单单次消费接口
@app.route("/consume")
def consume():
    order_id = request.args.get("orderId")
    if order_id in paid_orders:
        paid_orders.remove(order_id)
    return jsonify({"ok": True})

# Render保活接口
@app.route("/health")
def health():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
