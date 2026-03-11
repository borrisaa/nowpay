from flask import Flask, request, jsonify, redirect
import requests
import hashlib
import hmac

app = Flask(__name__)

paid_orders = set()

# 你的配置（和后台一致）
NOWPAYMENTS_API_KEY = "QBT21RV-SWQ4J79-KQNZD1P-QNSYH77"
NOWPAYMENTS_IPN_SECRET = "x9GiujGXpovf0c947GkQWrdgTon9Bxcr"  # 对应后台的 IPN secret key

# TRX 链 USDT 支付入口
@app.route("/pay_trx/<int:order_id>", methods=["GET"])
def create_payment_trx(order_id):
    order_id_str = str(order_id)
    headers = {
        "x-api-key": NOWPAYMENTS_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "price_amount": 15,
        "price_currency": "usd",
        "pay_currency": "usdttrc20",
        "order_id": order_id_str
    }
    try:
        resp = requests.post(
            "https://api.nowpayments.io/v1/payment",
            headers=headers,
            json=data,
            timeout=20
        )
        if resp.status_code == 201:
            res = resp.json()
            payment_id = res.get("payment_id")
            if payment_id:
                pay_url = f"https://nowpayments.io/payment/?iid={payment_id}"
                return redirect(pay_url)
            else:
                print(f"[ERROR TRX] 订单 {order_id_str} 未拿到 payment_id: {res}", flush=True)
        else:
            print(f"[ERROR TRX] 订单 {order_id_str} API 返回 {resp.status_code}: {resp.text}", flush=True)
    except Exception as e:
        print(f"[ERROR TRX] 订单 {order_id_str} 请求异常: {str(e)}", flush=True)
    return "Payment link failed", 500

# BSC 链 USDT 支付入口
@app.route("/pay_bsc/<int:order_id>", methods=["GET"])
def create_payment_bsc(order_id):
    order_id_str = str(order_id)
    headers = {
        "x-api-key": NOWPAYMENTS_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "price_amount": 15,
        "price_currency": "usd",
        "pay_currency": "usdtbsc",
        "order_id": order_id_str
    }
    try:
        resp = requests.post(
            "https://api.nowpayments.io/v1/payment",
            headers=headers,
            json=data,
            timeout=20
        )
        if resp.status_code == 201:
            res = resp.json()
            payment_id = res.get("payment_id")
            if payment_id:
                pay_url = f"https://nowpayments.io/payment/?iid={payment_id}"
                return redirect(pay_url)
            else:
                print(f"[ERROR BSC] 订单 {order_id_str} 未拿到 payment_id: {res}", flush=True)
        else:
            print(f"[ERROR BSC] 订单 {order_id_str} API 返回 {resp.status_code}: {resp.text}", flush=True)
    except Exception as e:
        print(f"[ERROR BSC] 订单 {order_id_str} 请求异常: {str(e)}", flush=True)
    return "Payment link failed", 500

# ✅ 关键修改：接口名从 /ipn 改成 /webhook，和后台完全一致
@app.route("/webhook", methods=["POST"])
def webhook_handler():
    try:
        raw_data = request.get_data()
        signature = request.headers.get("x-nowpayments-sig")
        
        # 签名验证（必须，防止伪造）
        computed_sig = hmac.new(
            NOWPAYMENTS_IPN_SECRET.encode(),
            raw_data,
            hashlib.sha512
        ).hexdigest()
        if not hmac.compare_digest(computed_sig, signature):
            return "Invalid signature", 403
        
        data = request.get_json()
        order_id = data.get("order_id")
        status = data.get("payment_status")
        
        if status == "finished" and order_id:
            paid_orders.add(order_id)
            print(f"[Webhook] 订单 {order_id} 支付成功", flush=True)
        
        return "OK", 200
    except Exception as e:
        print(f"[Webhook] 错误: {str(e)}", flush=True)
        return "Error", 500

# 机器人查询订单状态
@app.route("/check", methods=["GET"])
def check_order():
    order_id = request.args.get("orderId")
    return jsonify({"paid": order_id in paid_orders})

# 健康检查
@app.route("/health")
def health():
    return "running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
