import os

from volcenginesdkarkruntime import Ark


# For more information，please check this document（https://www.volcengine.com/docs/82379/1263279）
client = Ark(api_key=os.environ.get("ARK_API_KEY"))


if __name__ == "__main__":
    resp = client.chat.completions.create(
        model="doubao-seed-2-0-pro-260215",
        messages=[{"content":"请问你是哪个具体的模型？api调用费用是多少？","role":"user"}],
    )
        
    # 深度思考模型，且触发了深度思考，打印思维链内容
    if hasattr(resp.choices[0].message, 'reasoning_content'):
        print(resp.choices[0].message.reasoning_content)
        
    print(resp.choices[0].message.content)