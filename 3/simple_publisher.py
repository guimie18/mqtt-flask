import paho.mqtt.client as mqtt
import time

# MQTT 服务器配置
broker_address = "127.0.0.1"
broker_port = 1883
topic = "/my/test/message"
client_id = "simple_python_publisher"

# 定义回调函数
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("Connected successfully to broker")
        # 订阅自己的主题以验证发送
        client.subscribe(topic)
        print(f"Subscribed to topic: {topic}")
    else:
        print(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    print(f"Received message: '{msg.payload.decode()}' on topic: '{msg.topic}'")

# 创建 MQTT 客户端实例
try:
    # 针对 paho-mqtt 2.0+ 版本
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=client_id)
except AttributeError:
    # 针对 paho-mqtt 1.x 版本
    client = mqtt.Client(client_id=client_id)

# 设置回调函数
client.on_connect = on_connect
client.on_message = on_message

# 连接到 MQTT 代理
try:
    client.connect(broker_address, broker_port)
    # 启动后台循环
    client.loop_start()
    print(f"Connected to MQTT Broker: {broker_address}:{broker_port}")
except Exception as e:
    print(f"Connection failed: {e}")
    exit(1)

# 发布一条消息
message = "Hello, MQTT from Python!"
result = client.publish(topic, message)

if result.rc == mqtt.MQTT_ERR_SUCCESS:
    print(f"Successfully published message: '{message}' to topic '{topic}'")
else:
    print(f"Failed to publish message. Error code: {result.rc}")

# 等待一小段时间，确保消息发送
time.sleep(1)

# 断开连接
client.disconnect()
print("Disconnected from MQTT Broker.")
