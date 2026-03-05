from flask import Flask, request, jsonify
import hmac
import hashlib
import requests

app = Flask(__name__)

# 从 NowPayments 后台复制的 IPN Secret Key
IPN_SECRET_KEY = "QBT21RV-SWQ4J79-KQNZD1P-QNSYH77"
# 你的 Telegram Bot Token
TELEGRAM_BOT_TOKEN = "8699187838:AAGXy7zTKo1_LJEPD1dhnKekwn03EM07sdo"
# 你的 Telegram 用户ID（或频道ID），用于接收通知
TELEGRAM_CHAT_ID = "8404531662"

def verify_signature(data, signature):
    """验证 NowPayments 回调签名"""
    computed_signature = hmac.new(
        IPN_SECRET_KEY.encode(),
        data.encode(),
        hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(computed_signature, signature)

def send_telegram_notification(message):
    """向 Telegram 发送通知"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    requests.post(url, data=payload)

@app.route('/nowpayments-callback', methods=['POST'])
def nowpayments_callback():
    # 获取请求体和签名
    data = request.get_data(as_text=True)
    signature = request.headers.get('x-nowpayments-sig')
    
    # 验证签名
    if not verify_signature(data, signature):
        return jsonify({"status": "invalid signature"}), 403
    
    # 解析支付数据
    payment_data = request.json
    order_id = payment_data.get('order_id')
    amount = payment_data.get('amount')
    currency = payment_data.get('currency')
    status = payment_data.get('payment_status')
    
    # 处理支付成功
    if status == 'finished':
        message = f"✅ 支付成功！\n订单号: {order_id}\n金额: {amount} {currency}"
        send_telegram_notification(message)
        return jsonify({"status": "success"})
    
    return jsonify({"status": "received"})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)