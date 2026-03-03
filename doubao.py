import streamlit as st
import os
from volcenginesdkarkruntime import Ark

# --- 页面配置 ---
st.set_page_config(
    page_title="豆包 2.0 AI 助手", 
    page_icon="🌋",
    layout="wide"
)

# --- 样式优化 ---
st.markdown("""
<style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .stButton button {
        width: 100%;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    /* 深度思考样式 */
    .reasoning-box {
        background-color: #f8f9fa;
        border-left: 3px solid #6c757d;
        padding: 10px;
        margin-bottom: 10px;
        font-size: 0.9em;
        color: #555;
    }
</style>
""", unsafe_allow_html=True)

# --- 定价策略 ---
# 单位: 元/百万token


def calculate_cost(model_id, prompt_tokens, completion_tokens):
    """
    根据模型ID和Token数量计算价格 (单位: 元)
    计算公式: (Token数 / 1,000,000) * 单价
    """
    price_input_per_million = 0
    price_output_per_million = 0
    
    # 豆包 2.0 Pro (doubao-seed-2-0-pro)
    if "doubao-seed-2-0-pro" in model_id or "doubao-seed-2.0-pro" in model_id:
        if prompt_tokens <= 32000:
            price_input_per_million = 3.2
            price_output_per_million = 16.0
        elif prompt_tokens <= 128000:
            price_input_per_million = 4.8
            price_output_per_million = 24.0
        else:
            price_input_per_million = 9.6
            price_output_per_million = 48.0
            
    # 豆包 2.0 Code (doubao-seed-2-0-code)
    elif "doubao-seed-2-0-code" in model_id or "doubao-seed-2.0-code" in model_id:
        if prompt_tokens <= 32000:
            price_input_per_million = 3.2
            price_output_per_million = 16.0
        elif prompt_tokens <= 128000:
            price_input_per_million = 4.8
            price_output_per_million = 24.0
        else:
            price_input_per_million = 9.6
            price_output_per_million = 48.0

    # 豆包 2.0 Lite (doubao-seed-2-0-lite)
    elif "doubao-seed-2-0-lite" in model_id or "doubao-seed-2.0-lite" in model_id:
        if prompt_tokens <= 32000:
            price_input_per_million = 0.6
            price_output_per_million = 3.6
        elif prompt_tokens <= 128000:
            price_input_per_million = 0.9
            price_output_per_million = 5.4
        else:
            price_input_per_million = 1.8
            price_output_per_million = 10.8
        
    # 豆包 2.0 Mini (doubao-seed-2-0-mini)
    elif "doubao-seed-2-0-mini" in model_id or "doubao-seed-2.0-mini" in model_id:
        if prompt_tokens <= 32000:
            price_input_per_million = 0.2
            price_output_per_million = 2.0
        elif prompt_tokens <= 128000:
            price_input_per_million = 0.4
            price_output_per_million = 4.0
        else:
            price_input_per_million = 0.8
            price_output_per_million = 8.0
        
    # 默认兜底 (按 Pro 第一阶梯估算)
    else:
        price_input_per_million = 3.2
        price_output_per_million = 16.0

    # 计算总价
    input_cost = (prompt_tokens / 1000000) * price_input_per_million
    output_cost = (completion_tokens / 1000000) * price_output_per_million
    
    return input_cost + output_cost, price_input_per_million, price_output_per_million

# --- 初始化状态 ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = 0
if "total_cost" not in st.session_state:
    st.session_state.total_cost = 0.0
if "remaining_tokens" not in st.session_state:
    st.session_state.remaining_tokens = 420000 
if "available_models" not in st.session_state:
    st.session_state.available_models = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# --- 侧边栏 ---
with st.sidebar:
    st.title("🌋 设置")
    
    # API Key 输入 (直接在前端输入，不再强制依赖文件)
    api_key_input = st.text_input(
        "火山引擎 API Key", 
        type="password", 
        value=st.session_state.api_key,
        help="请输入您的火山引擎 API Key (sk-...)"
    )
    
    if api_key_input:
        st.session_state.api_key = api_key_input
        
    if not st.session_state.api_key:
        st.warning("请先输入 API Key 以开始使用")
        st.stop()
    else:
        st.success("✅ API Key 已就绪")

    # Client 初始化
    try:
        client = Ark(api_key=st.session_state.api_key)
    except Exception as e:
        st.error(f"客户端初始化失败: {e}")
        st.stop()

    # 模型加载
    if not st.session_state.available_models:
        try:
            with st.spinner("正在获取模型列表..."):
                try:
                    models = client.models.list()
                    all_models = [m.id for m in models.data]
                    st.session_state.available_models = sorted(all_models, key=lambda x: (not 'seed-2-0' in x, x))
                except AttributeError:
                    # 备用列表
                    st.session_state.available_models = [
                        "doubao-seed-2-0-pro-260215",
                        "doubao-seed-2-0-lite-260215",
                        "doubao-seed-2-0-mini-260215",
                        "doubao-seed-2-0-code-260215"
                    ]
        except Exception as e:
            st.error(f"连接失败: {e}")
            st.session_state.available_models = ["doubao-seed-2-0-pro-260215"]

    # 模型选择
    default_idx = 0
    for i, m in enumerate(st.session_state.available_models):
        if "doubao-seed-2-0-pro" in m:
            default_idx = i
            break
            
    selected_model = st.selectbox(
        "选择模型", 
        st.session_state.available_models,
        index=default_idx
    )
    
    # 显示定价提示
    if "doubao-seed-2-0-pro" in selected_model or "doubao-seed-2-0-code" in selected_model:
        st.info("""
        💰 **Pro/Code 版阶梯定价 (元/百万token)**
        * **0-32k**: 输入 3.2 / 输出 16.0
        * **32k-128k**: 输入 4.8 / 输出 24.0
        * **>128k**: 输入 9.6 / 输出 48.0
        """)
    elif "doubao-seed-2-0-lite" in selected_model:
        st.info("""
        💰 **Lite 版阶梯定价 (元/百万token)**
        * **0-32k**: 输入 0.6 / 输出 3.6
        * **32k-128k**: 输入 0.9 / 输出 5.4
        * **>128k**: 输入 1.8 / 输出 10.8
        """)
    elif "doubao-seed-2-0-mini" in selected_model:
        st.info("""
        💰 **Mini 版阶梯定价 (元/百万token)**
        * **0-32k**: 输入 0.2 / 输出 2.0
        * **32k-128k**: 输入 0.4 / 输出 4.0
        * **>128k**: 输入 0.8 / 输出 8.0
        """)
    else:
        dummy_cost, in_p, out_p = calculate_cost(selected_model, 1, 1)
        st.info(f"💰 **当前定价 (元/百万token)**\n\n输入: {in_p}\n\n输出: {out_p}")

    st.divider()
    
    # 操作区
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ 清空历史"):
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("🔄 刷新状态"):
            st.rerun()

# --- 主界面 ---
st.title("🌋 豆包大模型 2.0 (Ark SDK)")

# 顶部指标卡片
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("当前模型", selected_model.split("-")[0] + "..." + selected_model.split("-")[-1])
with col2:
    st.metric("剩余 Token 配额", f"{st.session_state.remaining_tokens:,}")
with col3:
    st.metric("本次会话花费", f"¥{st.session_state.total_cost:.4f}")

st.divider()

# 聊天记录
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🤖"):
        if "reasoning_content" in message and message["reasoning_content"]:
             with st.expander("💭 深度思考 (Reasoning)", expanded=False):
                st.markdown(message["reasoning_content"])
        
        st.markdown(message["content"])
        
        if "usage" in message:
            u = message["usage"]
            cost = message.get("cost", 0)
            st.caption(f"📊 消耗: {u['total_tokens']} (In: {u['prompt_tokens']} / Out: {u['completion_tokens']}) | 💸 ¥{cost:.5f}")

# 输入框
if prompt := st.chat_input("与其对话，探索无限可能..."):
    # 用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # 助手回复
    with st.chat_message("assistant", avatar="🤖"):
        message_placeholder = st.empty()
        try:
            # 调用 Ark SDK
            response = client.chat.completions.create(
                model=selected_model,
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            )
            
            # 获取回复内容
            choice = response.choices[0]
            answer = choice.message.content
            
            # 获取深度思考内容
            reasoning_content = None
            if hasattr(choice.message, 'reasoning_content') and choice.message.reasoning_content:
                reasoning_content = choice.message.reasoning_content
                with st.expander("💭 深度思考 (Reasoning)", expanded=True):
                    st.markdown(reasoning_content)
            
            usage = response.usage
            
            # 计费 (使用新的阶梯计费函数)
            cost, applied_in_price, applied_out_price = calculate_cost(
                selected_model, 
                usage.prompt_tokens, 
                usage.completion_tokens
            )
            
            # 更新状态
            st.session_state.total_tokens += usage.total_tokens
            st.session_state.total_cost += cost
            st.session_state.remaining_tokens -= usage.total_tokens
            
            # 展示
            message_placeholder.markdown(answer)
            # 显示更详细的计费信息 (包括当前使用的费率)
            st.caption(f"📊 消耗: {usage.total_tokens} (In: {usage.prompt_tokens} / Out: {usage.completion_tokens}) | 💸 ¥{cost:.5f} (Rate: {applied_in_price}/{applied_out_price})")
            
            # 记录
            msg_data = {
                "role": "assistant",
                "content": answer,
                "usage": {
                    "total_tokens": usage.total_tokens,
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens
                },
                "cost": cost
            }
            if reasoning_content:
                msg_data["reasoning_content"] = reasoning_content
                
            st.session_state.messages.append(msg_data)
            
        except Exception as e:
            st.error(f"请求失败: {e}")
