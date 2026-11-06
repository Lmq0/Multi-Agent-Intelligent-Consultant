import streamlit as st
from workflow import build_graph
from core.log import logger

# 1. 设置网页的基本信息
st.set_page_config(page_title="多 Agent 智能顾问", page_icon="🤖", layout="wide")
st.title("🤖 多 Agent 智能顾问系统")
st.markdown("基于 LangGraph + DeepSeek + 本地 RAG 的智能协作团队")

# 2. 在侧边栏加一些说明
with st.sidebar:
    st.header("关于本项目")
    st.markdown("""
    **团队成员：**
    - 👑 **Supervisor**: 意图识别与任务分发
    - 🕵️ **Researcher**: 联网搜索最新情报
    - 📂 **Extractor**: 检索本地 PDF 知识库
    - 🧠 **Analyst**: 数据计算与报告生成
    """)
    st.divider()
    if st.button("🗑️ 清空对话记录"):
        st.session_state.messages = []
        st.rerun()

# 3. 初始化 Session State (存储聊天记录)
if "messages" not in st.session_state:
    st.session_state.messages = []

# 4. 渲染之前的聊天记录
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. 接收用户输入
if prompt := st.chat_input("请输入你想咨询的问题，例如：结合最新新闻，帮我算算学费..."):

    # 把用户的问题显示在界面上
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 开始调用我们的 LangGraph 多 Agent 系统
    with st.chat_message("assistant"):
        # 用一个状态框来展示 Agent 工作的过程
        with st.status("🤖 Agent 团队正在处理您的请求...", expanded=True) as status:
            st.write("👑 调度员正在分析意图...")

            # 构建图
            app = build_graph()

            # 使用 stream 模式来逐步获取各节点的执行结果
            final_advice = ""

            # 我们只传 topic，图内部会自动流转
            for chunk in app.stream({"topic": prompt}):
                for node_name, state in chunk.items():
                    # 根据节点名字，在界面上打印漂亮的进度提示
                    if node_name == "supervisor":
                        decision = state.get("next_step")
                        st.write(f"👑 调度员决策：执行路径 -> **{decision}**")
                    elif node_name == "researcher":
                        st.write("🕵️ 情报专员：已联网完成最新资料搜集...")
                    elif node_name == "extractor":
                        st.write("📂 资料专员：已从本地知识库提取完毕...")
                    elif node_name == "analyst":
                        st.write("🧠 首席分析师：正在调用代码解释器计算并撰写报告...")

                    # 如果走到了 chatbot（兜底）或 analyst，提取最终文本
                    if "final_advice" in state:
                        final_advice = state["final_advice"]

            # 流程结束，更新状态框
            status.update(label="✅ 分析完成！", state="complete", expanded=False)

        # 输出最终的结果
        st.markdown("### 📊 最终建议报告")
        st.markdown(final_advice)

        # 把 AI 的回答存入历史记录
        st.session_state.messages.append({"role": "assistant", "content": final_advice})