from flask import Flask, request, jsonify, redirect
import requests

app = Flask(__name__)

paid_orders = set()
order_map = {}

# 你的正确密钥
NOWPAYMENTS_API_KEY = "QBT21RV-SWQ4J79-KQNZD1P-QNSYH77"

# TRX 链 USDT 支付入口（NowPayments 标准代码：usdttrc20）
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
        "pay_currency": "usdttrc20",  # 必须传，NowPayments 识别的 TRC20 USDT 代码
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

# BSC 链 USDT 支付入口（NowPayments 标准代码：usdtbsc）
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
        "pay_currency": "usdtbsc",    # 必须传，NowPayments 识别的 BEP20 USDT 代码
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

# IPN 回调（可选，后面再配）
@app.route("/ipn", methods=["POST"])
def ipn_handler():
    try:
        data = request.get_json()
        order_id = data.get("order_id")
        status = data.get("payment_status")
        if status == "finished" and order_id:
            paid_orders.add(order_id)
        return "OK", 200
    except:
        return "ERR", 400

# 机器人查询接口
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
