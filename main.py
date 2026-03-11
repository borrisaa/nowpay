from flask import Flask, request, jsonify, redirect
import requests

app = Flask(__name__)

paid_orders = set()
order_map = {}

# 你的正确密钥
NOWPAYMENTS_API_KEY = "QBT21RV-SWQ4J79-KQNZD1P-QNSYH77"
NOWPAYMENTS_IPN_SECRET = "x9GiujGXpovf0c947GkQWrdgTon9Bxcr"

# TRX 链 USDT 支付入口（直接出二维码）
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
        "pay_currency": "usdttrc20",  # 固定 TRC20 USDT
        "order_id": order_id_str,
        "fixed_payment_id": True     # 强制跳过选币页
    }
    try:
        resp = requests.post(
            "https://api.nowpayments.io/v1/payment",
            headers=headers,
            json=data,
            timeout=15
        )
        if resp.status_code in (200, 201):
            res = resp.json()
            purchase_id = res.get("purchase_id")
            if purchase_id:
                order_map[order_id_str] = res
                pay_url = f"https://nowpayments.io/payment/?iid={purchase_id}"
                return redirect(pay_url)
            else:
                print(f"[ERROR TRX] 订单 {order_id_str} purchase_id 为空: {res}", flush=True)
        else:
            print(f"[ERROR TRX] 订单 {order_id_str} API 返回 {resp.status_code}: {resp.text}", flush=True)
    except Exception as e:
        print(f"[ERROR TRX] 订单 {order_id_str} 创建支付失败: {str(e)}", flush=True)
    return "Payment link failed", 500

# BSC 链 USDT 支付入口（直接出二维码）
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
        "pay_currency": "usdtbsc",    # 固定 BEP20 USDT
        "order_id": order_id_str,
        "fixed_payment_id": True      # 强制跳过选币页
    }
    try:
        resp = requests.post(
            "https://api.nowpayments.io/v1/payment",
            headers=headers,
            json=data,
            timeout=15
        )
        if resp.status_code in (200, 201):
            res = resp.json()
            purchase_id = res.get("purchase_id")
            if purchase_id:
                order_map[order_id_str] = res
                pay_url = f"https://nowpayments.io/payment/?iid={purchase_id}"
                return redirect(pay_url)
            else:
                print(f"[ERROR BSC] 订单 {order_id_str} purchase_id 为空: {res}", flush=True)
        else:
            print(f"[ERROR BSC] 订单 {order_id_str} API 返回 {resp.status_code}: {resp.text}", flush=True)
    except Exception as e:
        print(f"[ERROR BSC] 订单 {order_id_str} 创建支付失败: {str(e)}", flush=True)
    return "Payment link failed", 500

# IPN 回调（NowPayments 后台填写：http://121.41.42.32:10000/ipn）
@app.route("/ipn", methods=["POST"])
def ipn_handler():
    try:
        data = request.get_json()
        order_id = data.get("order_id")
        status = data.get("payment_status")
        if status == "finished" and order_id:
            paid_orders.add(order_id)
            print(f"[INFO] 订单 {order_id} 支付成功", flush=True)
        return "OK", 200
    except Exception as e:
        print(f"[ERROR IPN] 处理失败: {str(e)}", flush=True)
        return "ERR", 400

# 机器人查询支付状态接口
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
