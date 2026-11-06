from typing import TypedDict

class AgentState(TypedDict):
    topic: str
    web_info: str
    local_info: str
    final_advice: str
    next_step: str
    # 新增：调度员的决策 ('researcher', 'extractor', 'both', 'analyst')
    direct_reply: str  # 新增：如果是闲聊，直接把回答存这里