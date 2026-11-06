from core import AgentState
from core import llm
from core import logger


def direct_answer_node(state: AgentState):
    logger.info("💬 [Chatbot] 触发兜底机制，直接回答闲聊/简单问题...")

    prompt = f"你是一个友好的 AI 助手，请简短、礼貌地回应用户：{state['topic']}"
    response = llm.invoke(prompt).content

    return {"direct_reply": response, "final_advice": response}  # 同时赋给 final_advice 方便主程序输出