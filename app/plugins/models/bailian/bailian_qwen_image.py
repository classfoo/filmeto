import json
import os
import dashscope
from dashscope import MultiModalConversation

def text2img(prompt:str):
    messages = [
        {
            "role": "user",
            "content": [
                {"text": "一副典雅庄重的对联悬挂于厅堂之中，房间是个安静古典的中式布置，桌子上放着一些青花瓷，对联上左书“义本生知人机同道善思新”，右书“通云赋智乾坤启数高志远”， 横批“智启通义”，字体飘逸，中间挂在一着一副中国风的画作，内容是岳阳楼。"}
            ]
        }
    ]

    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx"
    api_key = os.getenv("DASHSCOPE_API_KEY")

    response = MultiModalConversation.call(
        api_key=api_key,
        model="qwen-image",
        messages=messages,
        result_format='message',
        stream=False,
        watermark=True,
        prompt_extend=True,
        negative_prompt='',
        size='720*1280'
    )

    if response.status_code == 200:
        resonposeBody = json.dumps(response, ensure_ascii=False)
        print(resonposeBody)
    else:
        print(f"HTTP返回码：{response.status_code}")
        print(f"错误码：{response.code}")
        print(f"错误信息：{response.message}")
        print("请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code")