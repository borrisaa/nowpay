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
# NowPayments 回调（极简调试版：只打印原始内容）
# ----------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    now = datetime.datetime.now()
    # 🔥 只打印最原始的回调内容和请求头，方便调试
    print(f"[{now}] 👉 回调原始内容: {request.get_data()}")
    print(f"[{now}] 👉 回调头信息: {dict(request.headers)}")
    
    # 先不做复杂解析，只保证返回200让NOWPayments确认
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
