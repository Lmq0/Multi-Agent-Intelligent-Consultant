import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["MODELSCOPE_TRUST_REMOTE_CODE"] = "True"
# 2. 强制 Python 走你的本地梯子代理 (注意把 7890 换成你实际的端口)
#os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
from typing import TypedDict, Annotated
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_tavily import TavilySearch

# 新增的 RAG 依赖
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# ==========================================
# 1. 初始化大模型 (DeepSeek)
# ==========================================
os.environ["OPENAI_API_KEY"] = "sk-de17a8be53534776a3f63d659d529e1f"
os.environ["TAVILY_API_KEY"] = "tvly-你的Tavily_API_Key"
# 注意：DeepSeek 没有提供 Embedding（向量化）接口，所以我们借用免费的本地 Embedding 或者 OpenAI 的。
# 这里为了不让你花钱，用最简单的本地 Hash 向量化（效果一般但够演示），或者用阿里/OpenAI的。

# 1. 引入纯正的 HuggingFaceEmbeddings（不用魔搭的封装了）
from langchain_huggingface import HuggingFaceEmbeddings
import os

# 2. 让 HuggingFace 去魔搭的默认缓存文件夹里找模型
# 魔搭下载的默认路径一般在你的用户目录下的 .cache/modelscope/hub
os.environ["HF_HOME"] = os.path.expanduser("~/.cache/modelscope/hub")

print("正在加载本地向量模型...")
# 3. 强制开启 trust_remote_code，并指定路径
print("正在从本地文件夹直接加载模型...")
# 只需要保留这个路径，它绝对不联网
embeddings = HuggingFaceEmbeddings(model_name="./all-MiniLM-L6-v2")
print("模型加载完毕！")

llm = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com/v1",
    temperature=0
)

# ==========================================
# add. 离线处理 PDF，建立本地知识库
# ==========================================
print("1. 正在读取 PDF ...")  # <--- 加上这行
loader = PyPDFLoader("test_doc.pdf")
docs = loader.load()
print(f"2. PDF 读取完成，共 {len(docs)} 页。开始切片 ...") # <--- 加上这行

text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
splits = text_splitter.split_documents(docs)
print(f"3. 切片完成，共 {len(splits)} 个文本块。开始向量化并存入数据库（这一步没进度条，请耐心等）...") # <--- 加上这行

vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings, persist_directory="./chroma_db")
print("4. 向量库建立完成！") # <--- 加上这行

retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# 初始化网络搜索工具
search_tool = TavilySearch(max_results=3)


# 把长文本切块，方便检索
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
splits = text_splitter.split_documents(docs)

# 存入本地的 Chroma 数据库（会在当前目录生成一个 chroma_db 文件夹）
vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings, persist_directory="./chroma_db")
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})  # 每次检索最相关的 2 段


# ==========================================
# 3. 定义工具：把向量库包装成“查文档”工具
# ==========================================
@tool
def search_document(query: str) -> str:
    """当你需要回答关于 PDF 文档里的具体内容时，使用这个工具检索文档。"""
    print(f"\n[Tool执行] 正在文档库中检索：{query}")
    results = retriever.invoke(query)
    # 把检索到的段落拼成字符串返回
    return "\n\n".join([doc.page_content for doc in results])


tools = [search_document]
llm_with_tools = llm.bind_tools(tools)


# ==========================================
# 4. 定义状态、节点和路由（和上次一样，完全复用）
# ==========================================
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def assistant_node(state: AgentState):
    print("\n[Node] -> 进入大模型思考节点")
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


def tool_node(state: AgentState):
    print("\n[Node] -> 进入工具执行节点")
    last_message = state["messages"][-1]
    tool_messages = []
    for tool_call in last_message.tool_calls:
        selected_tool = next(t for t in tools if t.name == tool_call["name"])
        result = selected_tool.invoke(tool_call["args"])
        tool_messages.append(
            ToolMessage(content=str(result), tool_call_id=tool_call["id"])
        )
    return {"messages": tool_messages}


def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "continue_to_tools"
    return "end"


# ==========================================
# 5. 构建流程图
# ==========================================
workflow = StateGraph(AgentState)
workflow.add_node("assistant", assistant_node)
workflow.add_node("tools", tool_node)
workflow.add_edge(START, "assistant")

workflow.add_conditional_edges(
    "assistant",
    should_continue,
    {"continue_to_tools": "tools", "end": END}
)
workflow.add_edge("tools", "assistant")

app = workflow.compile()


# ==========================================
# 6. 运行测试
# ==========================================
if __name__ == "__main__":
    print("=== Agent 启动 ===")
    # 故意问一个只有 PDF 里才有的细节，逼它去查库
    inputs = {"messages": [HumanMessage(content="请帮我查一下这份文档，里面主要讲了什么内容？提取两个核心要点。")]}

    for output in app.stream(inputs):
        for key, value in output.items():
            if key == "assistant":
                msg = value["messages"][-1]
                if msg.content:
                    print(f"\n大模型最终回答:\n{msg.content}")