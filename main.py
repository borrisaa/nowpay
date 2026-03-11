from flask import Flask, request, jsonify, redirect
import datetime
import hmac
import hashlib

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
# NowPayments 回调（最终版：验证签名 + 识别订单）
# ----------------------
# 🔥 替换成你在 NowPayments 后台的 API Secret
NOWPAYMENTS_API_SECRET = "QBT21RV-SWQ4J79-KQNZD1P-QNSYH77"

@app.route("/webhook", methods=["POST"])
def webhook():
    now = datetime.datetime.now()
    print(f"[{now}] 👉 收到回调请求", flush=True)

    # 1. 读取请求头与原始数据
    signature = request.headers.get("X-NowPayments-Signature", "")
    raw_data = request.get_data()
    print(f"[{now}] 👉 回调签名: {signature}", flush=True)
    print(f"[{now}] 👉 回调原始字节: {raw_data}", flush=True)

    # 2. 验证 HMAC 签名（NowPayments 官方要求）
    computed_hmac = hmac.new(
        NOWPAYMENTS_API_SECRET.encode("utf-8"),
        raw_data,
        hashlib.sha512
    ).hexdigest()
    print(f"[{now}] 👉 计算签名: {computed_hmac}", flush=True)
    print(f"[{now}] 👉 签名验证结果: {computed_hmac == signature}", flush=True)

    # 3. 解析 JSON 回调数据
    data = request.get_json(silent=True) or {}
    print(f"[{now}] 👉 解析后 JSON: {data}", flush=True)

    # 4. 多路径匹配 Payment ID（兼容 NowPayments 各种返回格式）
    order_id = (
        data.get("payment_id")
        or data.get("orderId")
        or data.get("order_id")
        or data.get("id")
        or data.get("invoice_id")
        or str(data.get("payment", {}).get("id"))
        or data.get("metadata", {}).get("order_id")
    )

    # 5. 识别支付状态
    status = data.get("status") or data.get("payment_status")
    print(f"[{now}] 👉 识别到订单号: {order_id}, 状态: {status}", flush=True)

    # 6. 标记为已付款
    if order_id and status in ["confirmed", "finished", "success", "completed", "paid"]:
        paid_orders.add(str(order_id))
        print(f"[{now}] ✅ 订单 {order_id} 已成功标记为已付款！", flush=True)

    return "ok", 200

# ----------------------
# 查询支付状态
# ----------------------
@app.route("/check", methods=["GET"])
def check():
    order_id = request.args.get("orderId") or request.args.get("order_id")
    is_paid = str(order_id) in paid_orders
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

