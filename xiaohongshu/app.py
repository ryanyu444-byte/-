# coding=utf-8
"""
小红书内容生成工具 —— Streamlit 应用

功能：
  1. 输入主题关键词
  2. AI 自动生成 5 个爆款标题
  3. AI 自动生成约 800 字小红书正文
  4. AI 自动生成封面文案

运行方式：
  streamlit run xiaohongshu/app.py
"""

import streamlit as st
from generator import create_client, generate_content

# ---------------------------------------------------------------------------
# 页面配置
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="小红书内容生成器",
    page_icon="📕",
    layout="centered",
)

# ---------------------------------------------------------------------------
# 自定义样式
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .title-card {
        background: linear-gradient(135deg, #FF2442 0%, #FF6B81 100%);
        padding: 1.5rem 2rem;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .title-card h1 {
        margin: 0;
        font-size: 2rem;
        color: white;
    }
    .title-card p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1rem;
        color: white;
    }
    .result-section {
        background: #fafafa;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #f0f0f0;
    }
    .cover-text-box {
        background: linear-gradient(135deg, #FF2442 0%, #FF6B81 100%);
        color: white;
        font-size: 1.8rem;
        font-weight: bold;
        text-align: center;
        padding: 2.5rem 2rem;
        border-radius: 16px;
        margin: 0.5rem 0;
        letter-spacing: 2px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 页面头部
# ---------------------------------------------------------------------------
st.markdown("""
<div class="title-card">
    <h1>📕 小红书内容生成器</h1>
    <p>输入主题，一键生成爆款标题 + 正文 + 封面文案</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 侧边栏 - AI 配置
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ AI 模型配置")

    st.markdown("使用 [LiteLLM](https://docs.litellm.ai/docs/providers) 格式，支持 100+ 模型。")

    model = st.text_input(
        "模型名称",
        value="deepseek/deepseek-chat",
        help="格式：provider/model，如 openai/gpt-4o、deepseek/deepseek-chat",
    )
    api_key = st.text_input(
        "API Key",
        type="password",
        help="对应模型提供商的 API Key",
    )
    api_base = st.text_input(
        "API Base URL（可选）",
        value="",
        help="自定义 API 地址，留空则使用默认",
    )

    st.divider()
    st.markdown("""
    **常用模型示例：**
    - `deepseek/deepseek-chat`
    - `openai/gpt-4o`
    - `openai/gpt-4o-mini`
    - `anthropic/claude-3-5-sonnet-20241022`
    - `zhipu/glm-4-flash`

    使用 `openai/xxx` + 自定义 Base URL 可接入任意兼容接口。
    """)

# ---------------------------------------------------------------------------
# 主区域 - 输入 & 生成
# ---------------------------------------------------------------------------
topic = st.text_input(
    "🎯 输入你的笔记主题",
    placeholder="例如：大学生如何高效学习、30天瘦10斤的真实经历、平价好物推荐...",
)

generate_btn = st.button("✨ 一键生成内容", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# 生成逻辑
# ---------------------------------------------------------------------------
if generate_btn:
    if not topic.strip():
        st.warning("请输入一个主题关键词再生成哦～")
        st.stop()

    if not api_key.strip():
        st.warning("请在左侧边栏填写 API Key。")
        st.stop()

    client = create_client(model, api_key, api_base)
    valid, err = client.validate_config()
    if not valid:
        st.error(f"配置校验失败：{err}")
        st.stop()

    with st.spinner("🚀 AI 正在努力创作中，请稍候（约 15-30 秒）..."):
        try:
            result = generate_content(client, topic.strip())
        except Exception as e:
            st.error(f"生成失败：{e}")
            st.stop()

    st.success("🎉 内容生成完成！")

    # ----- 标题部分 -----
    st.markdown("### 📝 爆款标题（5选1）")
    for i, title in enumerate(result["titles"], 1):
        st.markdown(f"**{i}.** {title}")

    st.divider()

    # ----- 正文部分 -----
    st.markdown("### 📄 笔记正文")
    st.markdown(f'<div class="result-section">{result["content"]}</div>', unsafe_allow_html=True)

    st.divider()

    # ----- 封面文案 -----
    st.markdown("### 🎨 封面文案")
    st.markdown(f'<div class="cover-text-box">{result["cover_text"]}</div>', unsafe_allow_html=True)

    st.divider()

    # ----- 一键复制区 -----
    st.markdown("### 📋 一键复制")

    copy_titles = "\n".join(f"{i}. {t}" for i, t in enumerate(result["titles"], 1))
    st.text_area("标题（复制用）", value=copy_titles, height=160)
    st.text_area("正文（复制用）", value=result["content"], height=300)
    st.text_area("封面文案（复制用）", value=result["cover_text"], height=68)
