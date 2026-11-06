from core.state import AgentState
from skills.web_search import search_tool
from core.log import logger, log_node_execution

def researcher_node(state: AgentState):
    with log_node_execution("Researcher"):
        logger.info(f"🕵️ [Agent 1] 情报专员正在全网搜索关于【{state['topic']}】的最新动态...")
        query = f"{state['topic']} 最新政策 新闻 经验分享"
        search_result = search_tool.invoke(query)
        return {"web_info": str(search_result)}