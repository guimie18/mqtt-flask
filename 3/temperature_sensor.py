import paho.mqtt.client as mqtt
import time
import random
import json

# 配置 MQTT 服务器信息
broker_address = "127.0.0.1"  # MQTT 代理地址
broker_port = 1883  # MQTT 代理端口
topic = "/test/topic"  # 发布温度的主题
client_id = "temperature_sensor_01"  # 客户端 ID

# 创建 MQTT 客户端实例
try:
    # 针对 paho-mqtt 2.0+ 版本
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=client_id)
except AttributeError:
    # 针对 paho-mqtt 1.x 版本
    client = mqtt.Client(client_id=client_id)

# 定义回调函数
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("Connected successfully to broker")
    else:
        print(f"Connection failed with code {rc}")

# 设置回调函数
client.on_connect = on_connect

# 连接到 MQTT 代理
try:
    client.connect(broker_address, broker_port)
    # 启动后台循环
    client.loop_start()
    print(f"Connected to MQTT Broker: {broker_address}:{broker_port}")
except Exception as e:
    print(f"Connection failed: {e}")
    exit(1)

# 模拟温度传感器并发布消息
try:
    last_temperature = None
    while True:
        # 模拟 0-30 摄氏度范围内的温度
        current_temperature = round(random.uniform(0, 30), 2)

        if current_temperature != last_temperature:
            message_payload = {
                "sensor_id": client_id,
                "temperature": current_temperature,
                "timestamp": time.time()
            }
            message_json = json.dumps(message_payload)

            result = client.publish(topic, message_json)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"Published temperature: {current_temperature}°C to topic '{topic}'")
            else:
                print(f"Failed to publish message. Error code: {result.rc}")
            last_temperature = current_temperature
        
        time.sleep(5)  # 每 5 秒检查一次温度
except KeyboardInterrupt:
    print("Temperature sensor stopped by user. Exiting...")
finally:
    client.disconnect()
    print("Disconnected from MQTT Broker.")
