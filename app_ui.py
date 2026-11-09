### streamlit run app_ui.py
import streamlit as st
import os
from workflow import build_graph
from core.config import get_retriever,get_file_hash
from core.log import logger

st.set_page_config(page_title="多 Agent 智能顾问", page_icon="🤖", layout="wide")
st.title("🤖 多 Agent 智能顾问系统")

# ==========================================
# 侧边栏：文件上传与配置
# ==========================================
with st.sidebar:
    st.header("📁 企业知识库中心")

    # ==========================================
    # 核心修改：默认知识库兜底
    # ==========================================
    if "retriever" not in st.session_state:
        default_pdf = "./test_doc.pdf"  # 假设这是你放在根目录的默认文档
        if os.path.exists(default_pdf):
            with st.spinner("正在加载默认知识库..."):
                st.session_state["retriever"] = get_retriever(default_pdf)
                st.session_state["current_file"] = "默认手册 (test_doc.pdf)"
                st.session_state["current_hash"] = get_file_hash(default_pdf)
        else:
            st.session_state["retriever"] = None
            st.session_state["current_file"] = "无"

    # 文件上传区域
    uploaded_file = st.file_uploader("上传 PDF 文档注入知识库", type=["pdf"])

    if uploaded_file is not None:
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        file_hash = get_file_hash(file_path)

        if st.session_state.get("current_hash") != file_hash:
            with st.spinner("正在解析文档并建立向量索引..."):
                retriever = get_retriever(file_path)
                st.session_state["retriever"] = retriever
                st.session_state["current_file"] = uploaded_file.name
                st.session_state["current_hash"] = file_hash
            st.success(f"✅ 《{uploaded_file.name}》已入库！")

    st.info(f"📚 当前激活知识库：**{st.session_state.get('current_file', '无')}**")

    if st.button("🗑️ 清空对话记录"):
        st.session_state.messages = []
        st.rerun()

# ==========================================
# 主界面：聊天交互
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("请提问（可以上传 PDF 哦）..."):
    # 判断有没有上传文件
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("🤖 Agent 团队正在处理...", expanded=True) as status:
            app = build_graph()
            final_advice = ""

            # 注意：这里要把 retriever 一起传给图
            inputs = {
                "topic": prompt,
                "retriever": st.session_state["retriever"]  # 动态注入
            }

            try:  # <--- 加入 try
                for chunk in app.stream(inputs):
                    for node_name, state in chunk.items():
                        if node_name == "supervisor":
                            st.write(f"👑 调度员决策：执行路径 -> **{state.get('next_step')}**")
                        elif node_name == "researcher":
                            st.write("🕵️ 情报专员：已联网完成搜集...")
                        elif node_name == "extractor":
                            st.write("📂 资料专员：已从本地知识库提取完毕...")
                        elif node_name == "analyst":
                            st.write("🧠 首席分析师：正在计算并撰写报告...")

                        if "final_advice" in state:
                            final_advice = state["final_advice"]

                status.update(label="✅ 分析完成！", state="complete", expanded=False)
            except Exception as e:
                status.update(label="❌ 分析失败", state="error", expanded=False)
                st.error(f"系统繁忙或 API 额度不足，请稍后再试。报错信息：{str(e)[:100]}")
                final_advice = "抱歉，当前无法生成报告，请检查 API 余额。"



            st.markdown("### 📊 最终建议报告")
            st.markdown(final_advice)
            st.session_state.messages.append({"role": "assistant", "content": final_advice})