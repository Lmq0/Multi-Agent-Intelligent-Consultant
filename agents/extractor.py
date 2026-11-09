from core.state import AgentState
from core.log import logger, log_node_execution


def extractor_node(state: AgentState):
    with log_node_execution("Extractor"):
        logger.info(f"📂 [Agent 2] 资料专员正在翻阅本地手册...")

        dynamic_retriever = state.get("retriever")
        if not dynamic_retriever:
            return {"local_info": "用户尚未提供任何文档，无法提取本地资料。"}

        try:
            docs = dynamic_retriever.invoke(state['topic'])
            extracted_text = "\n".join([doc.page_content for doc in docs])
            return {"local_info": extracted_text}
        except Exception as e:
            logger.error(f"检索失败: {e}")
            return {"local_info": "本地资料检索失败。"}