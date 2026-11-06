from core.state import AgentState
from core.config import llm
from core.log import logger


def supervisor_node(state: AgentState):
    logger.info(f"👑 [Supervisor] 正在分析用户需求并制定调度计划...")

    prompt = f"""
    你是一个智能调度员。用户的请求是：【{state['topic']}】

    我们的团队有两个专家：
    1. researcher：负责联网搜索最新的新闻、政策、实时动态。
    2. extractor：负责去本地 PDF 知识库里查找手册、文档中的具体内容。

    请分析用户的请求，决定需要派发给谁。
    必须返回一个纯英文字符串，不能包含其他任何文字：
    - 如果输入是纯粹的打招呼（你好、你是谁）、闲聊、或者表达感谢，不需要查任何资料就能回答，返回: direct_answer
    - 如果只需要联网查最新信息，返回: researcher
    - 如果只需要查本地文档，返回: extractor
    - 如果既需要最新信息，又需要查文档，返回: both
    
    请严格只返回以上四个英文单词之一，不要输出任何标点或其他文字。
    """

    response = llm.invoke(prompt).content.strip().lower()

    # 容错处理：防止大模型输出多余的标点符号
    if "direct_answer" in response:
        decision = "direct_answer"
    elif "researcher" in response:
        decision = "researcher"
    elif "extractor" in response:
        decision = "extractor"
    elif "both" in response:
        decision = "both"
    else:
        decision = "both"  # 如果大模型发疯，默认全查一遍

    logger.info(f"👑 [Supervisor] 决策完成：我们需要调用 -> {decision}")
    return {"next_step": decision}