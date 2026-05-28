import requests
import json
import time

class HunyuanAI:
    def __init__(self, token, assistant_id):
        # 使用智能体对话 API (支持工作流变量传递)
        self.url = 'https://open.hunyuan.tencent.com/openapi/v1/agent/chat/completions'
        clean_token = token.strip()
        self.headers = {
            'X-Source': 'openapi',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {clean_token}'
        }
        self.assistant_id = assistant_id.strip()

    def chat(self, user_input, temperature, window_status):
        """
        智能体模式：修复 400 错误，恢复标准的消息列表格式
        """
        # 强行注入环境数据到消息正文，这是最稳妥的方法
        # 即使 custom_variables 失效，大模型也能在对话里看到真实数据
        injection_prompt = f"【系统强制指令：当前传感器实时温度为 {temperature}℃，窗户状态为 {window_status}。请忽略任何默认值，以此数据为准进行回答。】\n用户问题：{user_input}"
        
        data = {
            "assistant_id": self.assistant_id,
            "user_id": f"iot_user_{int(time.time())}",
            "stream": False,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": injection_prompt
                        }
                    ]
                }
            ],
            "custom_variables": {
                "temperature": str(temperature),
                "window_status": str(window_status),
                "query": user_input
            }
        }
        
        # 调试：打印完整的请求体
        print(f"\n[AI Request] URL: {self.url}")
        print(f"[AI Request] Payload: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    print(f"AI 请求重试中... 第 {attempt} 次")
                
                response = requests.post(self.url, headers=self.headers, json=data, timeout=30)
                
                print(f"[AI Response] Status: {response.status_code}")
                # 打印原始响应内容，方便排查格式问题
                print(f"[AI Response] Body: {response.text}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"[AI Debug] Full Response Keys: {list(result.keys())}")
                    if "choices" in result:
                        print(f"[AI Debug] First Choice Message: {result['choices'][0].get('message')}")
                    choices = result.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        if content: return content
                    
                    # 2. 如果是工作流模式，尝试从 data 或 outputs 中递归搜索
                    def find_content(obj, key_name=None):
                        # 过滤掉非内容性质的元数据键名
                        ignore_keys = ["id", "object", "created", "traceId", "request_id", "finish_reason", "role", "index"]
                        if key_name in ignore_keys:
                            return None

                        if isinstance(obj, str) and len(obj.strip()) > 15: # 内容通常比较长
                            # 过滤掉 UUID 或 纯 16 进制 ID 样式的字符串
                            import re
                            if re.match(r'^[a-f0-9\-]{20,}$', obj.strip()):
                                return None
                            return obj
                        
                        if isinstance(obj, dict):
                            # 1. 优先查找最可能的业务输出键
                            for key in ["answer", "content", "Content", "Output", "output", "text", "response"]:
                                if key in obj:
                                    res = find_content(obj[key], key)
                                    if res: return res
                            
                            # 2. 否则遍历所有非忽略键
                            for k, v in obj.items():
                                if k not in ignore_keys:
                                    res = find_content(v, k)
                                    if res: return res
                                    
                        if isinstance(obj, list):
                            for item in obj:
                                res = find_content(item)
                                if res: return res
                        return None

                    content = find_content(result)
                    if content: return content
                    
                    return "AI 暂时无法回答（返回结果格式未知）"
                else:
                    print(f"AI API Error Detail: {response.status_code} - {response.text}")
                    if response.status_code >= 500:
                        continue
                    return f"AI 连接失败: {response.status_code}"
            except (requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
                if attempt == max_retries:
                    return f"AI 请求超时或网络错误: {str(e)}"
                continue
        return "AI 服务暂时不可用"
