from core import AgentState
from core import llm
from skills import python_tool
from langchain_core.messages import HumanMessage, ToolMessage
from core.log import logger




# 给分析师绑定代码工具
llm_with_code = llm.bind_tools([python_tool])


def analyst_node(state: AgentState):
    logger.info("🧠 [Agent 3] 总顾问正在提取数据并计算...")

    # 核心修改：使用 .get()，如果没查到数据，就返回默认值，防止 KeyError
    web_data = state.get('web_info', '无外部情报')
    local_data = state.get('local_info', '无本地文档信息')

    prompt = f"""
    你是一位资深的财务与留学规划导师。请根据以下信息回答关于【{state['topic']}】的问题。

    【外部情报】：{web_data}
    【本地资料】：{local_data}

    要求：如果需要计算费用、比例，请务必写 Python 代码用工具执行计算。给出 3 个核心注意事项。
    """

    messages = [HumanMessage(content=prompt)]
    response = llm_with_code.invoke(messages)
    messages.append(response)

    if response.tool_calls:
        logger.info("  -> 发现需要计算，正在调用 Python 代码解释器...")
        for tool_call in response.tool_calls:
            tool_result = python_tool.invoke(tool_call["args"])
            messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"]))
        logger.info("  -> 计算完毕，正在生成最终建议...")
        final_response = llm.invoke(messages)
        return {"final_advice": final_response.content}
    else:
        logger.info("  -> 无需计算，直接生成最终建议...")
        return {"final_advice": response.content}