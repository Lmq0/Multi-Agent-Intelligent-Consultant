from core.state import AgentState
from core.config import retriever
from core.log import logger, log_node_execution

def extractor_node(state: AgentState):
    with log_node_execution("Extractor"):
        logger.info(f"📂 [Agent 2] 资料专员正在翻阅本地手册，提取关于【{state['topic']}】的细节...")
        docs = retriever.invoke(state['topic'])
        extracted_text = "\n".join([doc.page_content for doc in docs])
        return {"local_info": extracted_text}