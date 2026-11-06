import os
from typing import TypedDict
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END
from langchain_experimental.tools import PythonREPLTool
from langchain_core.messages import HumanMessage, ToolMessage

# ==========================================
# 1. 环境与模型初始化
# ==========================================
os.environ["OPENAI_API_KEY"] = "sk-de17a8be53534776a3f63d659d529e1f"
os.environ["TAVILY_API_KEY"] = "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"

# 初始化 Python 代码执行器
python_tool = PythonREPLTool()

llm = ChatOpenAI(model="deepseek-chat", base_url="https://api.deepseek.com/v1", temperature=0)

llm_with_code = llm.bind_tools([python_tool])

# 加载你本地的向量模型（请确保路径对，或者你缓存里有）
embeddings = HuggingFaceEmbeddings(model_name="./all-MiniLM-L6-v2")

# 初始化本地知识库（这里假设你的 test_doc.pdf 是一份留学指南或招聘 JD）
loader = PyPDFLoader("test_doc.pdf")
docs = loader.load()
splits = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_documents(docs)
vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings, persist_directory="./chroma_db")
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# 初始化网络搜索工具
search_tool = TavilySearch(max_results=3)


# ==========================================
# 2. 定义团队共享状态 (State)
# ==========================================
class AgentState(TypedDict):
    topic: str  # 调研主题（比如 "新加坡留学" 或 "某公司面试"）
    web_info: str  # 网络情报
    local_info: str  # 本地文档信息
    final_advice: str  # 最终建议


# ==========================================
# 3. 定义三个 Agent 节点 (Nodes)
# ==========================================
def researcher_node(state: AgentState):
    """情报专员：负责网上搜最新的政策和新闻"""
    print(f"\n[Agent 1] 情报专员正在全网搜索关于【{state['topic']}】的最新动态...")
    query = f"{state['topic']} 最新政策 新闻 经验分享"
    search_result = search_tool.invoke(query)
    return {"web_info": str(search_result)}


def extractor_node(state: AgentState):
    """资料专员：负责去本地 PDF 查具体细节"""
    print(f"\n[Agent 2] 资料专员正在翻阅本地手册，提取关于【{state['topic']}】的细节...")
    docs = retriever.invoke(state['topic'])
    extracted_text = "\n".join([doc.page_content for doc in docs])
    return {"local_info": extracted_text}


def advisor_node(state: AgentState):
    """总顾问：先提取数据算账，再综合信息写报告"""
    print("\n[Agent 3] 总顾问正在提取数据并计算...")

    # 1. 先让大模型去梳理数据，如果需要算数，它会自己调用 Python 工具
    prompt = f"""
    你是一位资深的财务与留学规划导师。请根据以下信息回答关于【{state['topic']}】的问题。

    【外部情报】：{state['web_info']}
    【本地资料】：{state['local_info']}

    要求：
    1. 如果需要计算费用、比例（比如学费涨幅、总开销等），请务必写 Python 代码用工具执行计算，不要自己心算。
    2. 拿到计算结果后，给出 3 个核心注意事项和行动建议。
    """

    messages = [HumanMessage(content=prompt)]

    # 第一轮思考：大模型决定是否需要写代码
    response = llm_with_code.invoke(messages)
    messages.append(response)

    # 如果大模型说要调用代码工具（比如它写了计算学费的代码）
    if response.tool_calls:
        print("  -> 发现需要计算，正在调用 Python 代码解释器...")
        for tool_call in response.tool_calls:
            # 执行大模型写的 Python 代码
            tool_result = python_tool.invoke(tool_call["args"])
            # 把计算结果包装好，放回对话历史里
            messages.append(
                ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"])
            )

        # 2. 第二轮思考：大模型拿到精确的计算结果后，开始写最终报告
        print("  -> 计算完毕，正在生成最终建议...")
        final_response = llm.invoke(messages)
        return {"final_advice": final_response.content}

    else:
        # 如果不需要计算，直接输出报告
        print("  -> 无需计算，直接生成最终建议...")
        return {"final_advice": response.content}


# ==========================================
# 4. 构建多 Agent 协作图 (Graph)
# ==========================================
workflow = StateGraph(AgentState)
workflow.add_node("Researcher", researcher_node)
workflow.add_node("Extractor", extractor_node)
workflow.add_node("Advisor", advisor_node)

# 流水线：搜网络 -> 查本地 -> 写建议
workflow.add_edge(START, "Researcher")
workflow.add_edge("Researcher", "Extractor")
workflow.add_edge("Extractor", "Advisor")
workflow.add_edge("Advisor", END)

app = workflow.compile()

# ==========================================
# 5. 运行测试
# ==========================================
if __name__ == "__main__":
    print("=== 留学与求职智能顾问团启动 ===")
    # 你可以把 topic 换成你关心的话题，比如 "新加坡NTU MSAI硕士就业"
    # 注意：本地 PDF 里最好也有相关内容，不然 Extractor 查出来的是空的
    inputs = {"topic": "我第一年学费 50000 新币，第二年涨了 15%，两年生活费每年 20000 新币。请帮我算算两年总共要花多少人民币？（假设汇率 1 新币 = 5.4 人民币）"}

    result = app.invoke(inputs)

    print("\n" + "=" * 50)
    print(f"🎓 关于【{inputs['topic']}】的最终建议：")
    print("=" * 50)
    print(result["final_advice"])