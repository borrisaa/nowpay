from flask import Flask, request, jsonify
import hmac
import hashlib
import requests

# ===================== 你的信息已全部填好 =====================
BOT_TOKEN = "8699187838:AAGXy7zTKo1_LJEPD1dhnKekwn03EM07sdo"
IPN_SECRET = "x9GiujGXpovf0c947GkQWrdgTon9Bxcr"
PAY_AMOUNT = 15  # 15 USDT
# =================================================================

app = Flask(__name__)

# 1. 用户点开的付款验证页面
@app.route('/pay/<chat_id>')
def pay_page(chat_id):
    return f"""
    <html>
        <head>
            <meta charset="utf-8">
            <title>激活服务</title>
        </head>
        <body style="text-align:center; font-size:22px; margin-top:60px; font-family: Arial">
            <h3>请完成支付以激活服务</h3>
            <p>金额：{PAY_AMOUNT} USDT</p >
            <p>支付完成后自动激活</p >
            <br>
            <p style="font-size:14px; color:#666">
                此页面由系统自动生成，仅用于身份验证
            </p >
        </body>
    </html>
    """

# 2. NowPayments 回调通知（核心）
@app.route('/nowpayments-callback', methods=['POST'])
def nowpayments_callback():
    try:
        data = request.get_json()
        signature = request.headers.get('x-nowpayments-sig')

        if not signature:
            return "No signature", 403

        # 验证签名
        computed_sig = hmac.new(
            IPN_SECRET.encode(),
            request.get_data(),
            hashlib.sha512
        ).hexdigest()

        if computed_sig != signature:
            return "Invalid signature", 403

        # 从订单号获取用户 chat_id
        order_id = data.get('order_id', '')
        amount = data.get('amount', 0)

        if order_id:
            # 通知用户付款成功
            msg = f"✅ 支付成功！\n金额：{amount} USDT\n已为您激活服务。"
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": order_id, "text": msg}
            )

        return "OK", 200

    except Exception as e:
        return "Error", 500

# 3. 给扣子机器人调用：生成付款链接
@app.route('/create-pay-link')
def create_pay_link():
    chat_id = request.args.get('chat_id', '')
    if not chat_id:
        return jsonify({"error": "missing chat_id"}), 400

    host = request.host
    pay_link = f"https://{host}/pay/{chat_id}"

    return jsonify({
        "pay_link": pay_link
    })

@app.route('/')
def index():
    return "支付中间服务运行中 - 正常"

if __name__ == '__main__':
    app.run()
