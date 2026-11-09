import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from core.log import logger
load_dotenv()

# 初始化大模型
llm = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com/v1",
    temperature=0,
    api_key=os.getenv("DEEPSEEK_API_KEY")
)

# 加载本地向量模型
# ...
logger.info("正在加载本地向量模型...")
# ...
embeddings = HuggingFaceEmbeddings(model_name="./all-MiniLM-L6-v2") # 确保路径正确

# 初始化本地文档检索器
# ... 前面的 import 和 llm、embeddings 初始化保持不变 ...

def get_retriever(pdf_path: str):
    """接收一个 PDF 路径，动态解析并建立/加载向量库"""
    # 每次上传新文件，建一个新的数据库文件夹，避免污染旧的
    db_path = pdf_path.replace(".pdf", "_db")

    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    splits = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_documents(docs)

    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=db_path
    )
    return vectorstore.as_retriever(search_kwargs={"k": 2})


import hashlib


# ... 之前的 import ...

def get_file_hash(file_path: str) -> str:
    """计算文件的 MD5 哈希值，用于去重"""
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()[:10]  # 截取前10位当ID


def get_retriever_for_file(pdf_path: str):
    file_hash = get_file_hash(pdf_path)
    # 用哈希值做文件夹名，内容相同绝对不会重新建库
    db_path = f"./vector_dbs/db_{file_hash}"

    import os
    os.makedirs("./vector_dbs", exist_ok=True)

    # 如果这个库已经存在了，直接加载，不重新解析 PDF
    if os.path.exists(db_path):
        print(f"检测到已存在的向量库 {db_path}，直接加载。")
        vectorstore = Chroma(persist_directory=db_path, embedding_function=embeddings)
    else:
        print(f"未找到现有库，正在为 {pdf_path} 新建向量库...")
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        splits = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_documents(docs)
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory=db_path
        )

    return vectorstore.as_retriever(search_kwargs={"k": 2})