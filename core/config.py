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
def get_retriever():
    loader = PyPDFLoader("./test_doc.pdf") # 确保路径正确
    docs = loader.load()
    splits = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50).split_documents(docs)
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings, persist_directory="../chroma_db")
    return vectorstore.as_retriever(search_kwargs={"k": 2})

retriever = get_retriever()