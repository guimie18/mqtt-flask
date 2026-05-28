from flask import Flask, render_template, request, jsonify
import paho.mqtt.client as mqtt
import json
import threading
import time
from ai_helper import HunyuanAI

app = Flask(__name__)

# --- AI 配置 (在此填写你的腾讯混元信息) ---
AI_TOKEN = "fIpaA8EM2c1dQ3vrcODOJCK8hmqfZsc9"
AI_ASSISTANT_ID = "2057474655706606656"
ai_helper = HunyuanAI(AI_TOKEN, AI_ASSISTANT_ID)

# 全局变量存储最新数据
latest_temperature = 0.0
window_status = "opened"  # 默认为打开状态

# MQTT 配置
broker_address = "127.0.0.1"
broker_port = 1883
temp_topic = "/test/topic"
status_topic = "/test/window_status"
control_topic = "/test/window_control"

# 初始化 MQTT 客户端实例
try:
    # 针对 paho-mqtt 2.0+ 版本
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
except AttributeError:
    # 针对 paho-mqtt 1.x 版本
    mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.subscribe([(temp_topic, 0), (status_topic, 0)])
        print(f"Subscribed to {temp_topic} and {status_topic}")
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    global latest_temperature, window_status
    payload = msg.payload.decode()
    try:
        if msg.topic == temp_topic:
            # 解析温度数据
            data = json.loads(payload)
            if isinstance(data, dict) and "temperature" in data:
                latest_temperature = data["temperature"]
            else:
                latest_temperature = float(payload)
        elif msg.topic == status_topic:
            # 解析窗户状态数据
            data = json.loads(payload)
            window_status = data.get("status", "opened")
            print(f"Window status updated: {window_status}")
            
    except Exception as e:
        print(f"Error processing MQTT message on {msg.topic}: {e}")

def start_mqtt():
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    try:
        mqtt_client.connect(broker_address, broker_port)
        mqtt_client.loop_forever()
    except Exception as e:
        print(f"MQTT Connection Error: {e}")

# 在后台线程启动 MQTT 客户端
mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
mqtt_thread.start()

@app.route('/')
def index():
    return render_template('index.html', 
                           temperature=latest_temperature, 
                           window_status=window_status)

@app.route('/api/data')
def get_data():
    return jsonify({
        "temperature": latest_temperature,
        "window_status": window_status
    })

@app.route('/control/<action>')
def control_window(action):
    if mqtt_client and mqtt_client.is_connected():
        command = {"command": action, "timestamp": time.time()}
        mqtt_client.publish(control_topic, json.dumps(command))
        print(f"Published control command: {action}")
        return f"Command {action} sent"
    return "MQTT Client not connected", 500

@app.route('/ask_ai', methods=['POST'])
def ask_ai():
    print("--- 收到 AI 咨询请求 ---")
    try:
        data = request.json
        user_query = data.get('query')
        print(f"用户输入: {user_query}")
        
        # 确保温度是浮点数，防止比较出错
        current_temp = float(latest_temperature)
        print(f"正在调用腾讯混元 API (当前环境数据 - 温度: {current_temp}, 窗户: {window_status})...")
        
        # 调用 AI，传递独立变量
        answer = ai_helper.chat(user_query, current_temp, window_status)
        print(f"AI 回复最终结果: {answer}")
        
        # --- 联动控制逻辑 ---
        if mqtt_client and mqtt_client.is_connected():
            # 1. 优先根据 AI 的建议进行控制
            if "建议关窗" in answer or "应该关窗" in answer:
                mqtt_client.publish(control_topic, json.dumps({"command": "close", "timestamp": time.time()}))
                print(">>> AI 指令：执行关窗")
            elif "建议开窗" in answer or "应该开窗" in answer:
                mqtt_client.publish(control_topic, json.dumps({"command": "open", "timestamp": time.time()}))
                print(">>> AI 指令：执行开窗")
            
            # 2. 兜底逻辑：如果 AI 服务异常，执行硬编码规则
            elif "暂时不可用" in answer or "连接失败" in answer or "格式未知" in answer:
                print(f">>> AI 异常，进入系统兜底。当前判断温度: {current_temp}")
                if "开窗" in user_query or "适合" in user_query:
                    if current_temp > 25:
                        mqtt_client.publish(control_topic, json.dumps({"command": "open", "timestamp": time.time()}))
                        answer = f"AI 服务暂时不可用\n(系统兜底：AI 异常，但根据当前温度 {current_temp}℃ > 25℃ 已为您自动开窗)"
                        print(">>> 兜底逻辑：温度 > 25，执行开窗")
                    elif current_temp < 15:
                        mqtt_client.publish(control_topic, json.dumps({"command": "close", "timestamp": time.time()}))
                        answer = f"AI 服务暂时不可用\n(系统兜底：AI 异常，但根据当前温度 {current_temp}℃ < 15℃ 已为您自动关窗)"
                        print(">>> 兜底逻辑：温度 < 15，执行关窗")
                    else:
                        answer = f"AI 服务暂时不可用\n(系统兜底：AI 异常，当前温度 {current_temp}℃ 处于舒适区间，无需动作)"
                        print(">>> 兜底逻辑：温度舒适，不执行动作")
        
        return jsonify({"answer": answer})
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"!!! Flask 路由崩溃 !!!\n{error_msg}")
        return jsonify({"answer": f"系统内部错误: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
