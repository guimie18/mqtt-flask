import paho.mqtt.client as mqtt
import json
import time

# 配置 MQTT 服务器信息
broker_address = "127.0.0.1"  # MQTT 代理地址
broker_port = 1883  # MQTT 代理端口
temperature_topic = "/test/topic"  # 订阅温度的主题
window_status_topic = "/test/window_status" # 发布窗户状态的主题
control_topic = "/test/window_control" # 订阅网页控制的主题
client_id = "window_closer_01"  # 客户端 ID

window_closed = False # 窗户状态

# MQTT 客户端回调函数 - 连接成功
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"Connected to MQTT Broker with result code {rc}")
        # 订阅温度主题和网页控制主题
        client.subscribe([(temperature_topic, 0), (control_topic, 0)])
        print(f"Subscribed to: {temperature_topic} and {control_topic}")
    else:
        print(f"Connection failed with code {rc}")

# MQTT 客户端回调函数 - 收到消息
def on_message(client, userdata, msg):
    global window_closed
    try:
        payload = json.loads(msg.payload.decode())
        
        # 处理温度自动控制逻辑
        if msg.topic == temperature_topic:
            temperature = payload.get("temperature")
            if temperature is not None:
                print(f"Received temperature: {temperature}°C")
                if temperature < 10 and not window_closed:
                    update_window_status(client, True, f"temperature_below_{temperature}°C")
                elif temperature >= 10 and window_closed:
                    update_window_status(client, False, f"temperature_above_{temperature}°C")

        # 处理网页远程控制逻辑
        elif msg.topic == control_topic:
            command = payload.get("command")
            print(f"Received remote command: {command}")
            if command == "close" and not window_closed:
                update_window_status(client, True, "remote_control")
            elif command == "open" and window_closed:
                update_window_status(client, False, "remote_control")

    except json.JSONDecodeError:
        print(f"Failed to decode JSON from message: {msg.payload.decode()}")
    except Exception as e:
        print(f"Error processing message: {e}")

def update_window_status(client, should_close, reason):
    global window_closed
    window_closed = should_close
    status_str = "closed" if should_close else "opened"
    action_str = "Closing" if should_close else "Opening"
    
    print(f"{action_str} window due to {reason}...")
    time.sleep(0.5) # 模拟动作延迟
    print(f"Window {status_str}.")
    
    # 发布状态更新
    message_payload = {
        "device_id": client_id,
        "status": status_str,
        "reason": reason,
        "timestamp": time.time()
    }
    client.publish(window_status_topic, json.dumps(message_payload))
    print(f"Published window status: {status_str} to topic '{window_status_topic}'")

# 创建 MQTT 客户端实例
try:
    # 针对 paho-mqtt 2.0+ 版本
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
except AttributeError:
    # 针对 paho-mqtt 1.x 版本
    client = mqtt.Client(client_id=client_id)
client.on_connect = on_connect
client.on_message = on_message

# 连接到 MQTT 代理
try:
    client.connect(broker_address, broker_port)
    print(f"Connecting to MQTT Broker: {broker_address}:{broker_port}")
except Exception as e:
    print(f"Connection failed: {e}")
    exit(1)

# 启动 MQTT 客户端循环
client.loop_forever()
