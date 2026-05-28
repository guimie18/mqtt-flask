import paho.mqtt.client as mqtt
import time

# 配置 MQTT 服务器信息
broker_address = "127.0.0.1" # MQTT 代理地址
broker_port = 1883 # MQTT 代理端口
topic = "/test/topic" # 发布和订阅的主题
client_id = "python_mqtt_client" # 客户端 ID

# 定义回调函数
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("Connected successfully to broker")
        # 连接成功后订阅主题
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
    # 启动后台循环以处理消息收发
    client.loop_start()
    print(f"Connected to MQTT Broker: {broker_address}:{broker_port}")
except Exception as e:
    print(f"Connection failed: {e}")
    exit(1)

# 开始循环
try:
    counter = 0
    while True:
        message = f"Message {counter}"
        # 发布消息
        result = client.publish(topic, message)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"Published message '{message}' to topic '{topic}'")
        else:
            print(f"Failed to publish message. Error code: {result.rc}")
        counter += 1
        # 等待 10 秒
        time.sleep(10)
except KeyboardInterrupt:
    print("Interrupted by user. Exiting...")
finally:
 # 断开连接
    client.disconnect()
 