from flask import Flask, request, jsonify, redirect
import datetime
import hmac
import hashlib

app = Flask(__name__)

# 内存订单（重启清空，简单模式）
paid_orders = set()

# 客户订单号 → NOWPayments payment_id 映射（核心绑定）
order_to_payment = {}

# 你自己的 NowPayments 固定支付链接（完全不变）
FIXED_PAY_URL = "https://nowpayments.io/payment/?iid=5874033439"
FIXED_PAY_URL_BSC = "https://nowpayments.io/payment/?iid=5845644542"

# 服务器回调地址（自动回调核心）
CALLBACK_URL = "http://121.41.42.32:10000/webhook"

# NowPayments IPN Secret（你原来的）
NOWPAYMENTS_API_SECRET = "x9GiujGXpovf0c947GkQWrdgTon9Bxcr"

# ----------------------
# TRX 支付入口
# ----------------------
@app.route("/pay/<int:order_id>", methods=["GET"])
def pay(order_id):
    order_id_str = str(order_id)
    pay_url = f"{FIXED_PAY_URL}&orderId={order_id_str}&callback_url={CALLBACK_URL}"
    if order_id_str not in order_to_payment:
        order_to_payment[order_id_str] = None
    return redirect(pay_url)

# ----------------------
# BSC 支付入口
# ----------------------
@app.route("/pay_bsc/<int:order_id>", methods=["GET"])
def pay_bsc(order_id):
    order_id_str = str(order_id)
    pay_url = f"{FIXED_PAY_URL_BSC}&orderId={order_id_str}&callback_url={CALLBACK_URL}"
    if order_id_str not in order_to_payment:
        order_to_payment[order_id_str] = None
    return redirect(pay_url)

# ----------------------
# NowPayments 自动/手动 回调（已完美兼容）
# ----------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    now = datetime.datetime.now()

    signature = request.headers.get("X-NowPayments-Signature", "")
    raw_data = request.get_data()

    print(f"[{now}] 收到回调", flush=True)
    print(f"[{now}] 回调签名: {signature}", flush=True)
    print(f"[{now}] 原始数据: {raw_data}", flush=True)

    computed_hmac = hmac.new(
        NOWPAYMENTS_API_SECRET.encode("utf-8"),
        raw_data,
        hashlib.sha512
    ).hexdigest()

    print(f"[{now}] 计算签名: {computed_hmac}", flush=True)
    print(f"[{"now"}] 验签结果: {computed_hmac == signature}", flush=True)

    data = request.get_json(silent=True) or {}
    print(f"[{now}] 回调JSON: {data}", flush=True)

    payment_id = str(data.get("payment_id") or data.get("payment", {}).get("id"))
    client_order_id = data.get("orderId") or data.get("order_id")
    status = data.get("status") or data.get("payment_status")

    print(f"[{now}] 客户订单号: {client_order_id}, payment_id: {payment_id}, 状态: {status}", flush=True)

    # 绑定映射（自动回调必走这里）
    if client_order_id and payment_id:
        order_to_payment[str(client_order_id)] = payment_id
        print(f"[{now}] 🔗 绑定映射: {client_order_id} → {payment_id}", flush=True)

    # 支付成功标记（自动回调成功就标记）
    if payment_id and status in ["finished", "confirmed", "success", "paid", "completed"]:
        paid_orders.add(payment_id)
        print(f"[{now}] ✅ 订单 {payment_id} 已标记付款成功", flush=True)

    return "ok", 200

# ----------------------
# Coze机器人查询接口（完全匹配格式）
# ----------------------
@app.route("/check", methods=["GET"])
def check():
    client_order_id = request.args.get("orderId") or request.args.get("order_id")
    if not client_order_id:
        return jsonify({"paid": False})
    
    payment_id = order_to_payment.get(str(client_order_id))
    if not payment_id:
        return jsonify({"paid": False})
    
    is_paid = payment_id in paid_orders
    return jsonify({"paid": is_paid})

# ----------------------
# 激活后销毁订单
# ----------------------
@app.route("/consume", methods=["GET"])
def consume():
    client_order_id = request.args.get("orderId") or request.args.get("order_id")
    if not client_order_id:
        return jsonify({"ok": False, "error": "缺少订单号"})
    
    payment_id = order_to_payment.get(str(client_order_id))
    if payment_id and payment_id in paid_orders:
        paid_orders.remove(payment_id)
    return jsonify({"ok": True})

# ----------------------
# 健康检查
# ----------------------
@app.route("/health", methods=["GET"])
def health():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)    raw_data = request.get_data()

    # 强制输出日志，不缓冲
    print(f"[{now}] 收到回调", flush=True)
    print(f"[{now}] 回调签名: {signature}", flush=True)
    print(f"[{now}] 原始数据: {raw_data}", flush=True)

    # 验签（玩票性质，失败也不影响）
    computed_hmac = hmac.new(
        NOWPAYMENTS_API_SECRET.encode("utf-8"),
        raw_data,
        hashlib.sha512
    ).hexdigest()

    print(f"[{now}] 计算签名: {computed_hmac}", flush=True)
    print(f"[{now}] 验签结果: {computed_hmac == signature}", flush=True)

    data = request.get_json(silent=True) or {}
    print(f"[{now}] 回调JSON: {data}", flush=True)

    # 提取关键信息
    payment_id = str(data.get("payment_id") or data.get("payment", {}).get("id"))
    client_order_id = data.get("orderId") or data.get("order_id")  # 这就是客户看到的订单号
    status = data.get("status") or data.get("payment_status")

    print(f"[{now}] 客户订单号: {client_order_id}, payment_id: {payment_id}, 状态: {status}", flush=True)

    # 绑定客户订单号和 payment_id
    if client_order_id and payment_id:
        order_to_payment[str(client_order_id)] = payment_id
        print(f"[{now}] 🔗 绑定映射: {client_order_id} → {payment_id}", flush=True)

    # 支付成功就标记 payment_id
    if payment_id and status in ["finished", "confirmed", "success", "paid", "completed"]:
        paid_orders.add(payment_id)
        print(f"[{now}] ✅ 订单 {payment_id} 已标记付款成功", flush=True)

    return "ok", 200

# ----------------------
# 查询支付状态（客户输入自己的订单号）
# ----------------------
@app.route("/check", methods=["GET"])
def check():
    client_order_id = request.args.get("orderId") or request.args.get("order_id")
    if not client_order_id:
        return jsonify({"paid": False, "error": "缺少订单号"})
    
    # 先查映射表，找到对应的 payment_id
    payment_id = order_to_payment.get(str(client_order_id))
    if not payment_id:
        return jsonify({"paid": False, "error": "订单未找到或未支付"})
    
    # 再查是否已支付
    is_paid = payment_id in paid_orders
    return jsonify({"paid": is_paid})

# ----------------------
# 激活后销毁订单
# ----------------------
@app.route("/consume", methods=["GET"])
def consume():
    client_order_id = request.args.get("orderId") or request.args.get("order_id")
    if not client_order_id:
        return jsonify({"ok": False, "error": "缺少订单号"})
    
    payment_id = order_to_payment.get(str(client_order_id))
    if payment_id and payment_id in paid_orders:
        paid_orders.remove(payment_id)
        # 可选：清理映射
        # del order_to_payment[str(client_order_id)]
    return jsonify({"ok": True})

# ----------------------
# 健康检查
# ----------------------
@app.route("/health", methods=["GET"])
def health():
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)

