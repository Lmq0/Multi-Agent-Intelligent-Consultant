from langgraph.graph import StateGraph, START, END
from core.state import AgentState
from agents.supervisor import supervisor_node
from agents.researcher import researcher_node
from agents.extractor import extractor_node
from agents.analyst import analyst_node
from agents.chatbot import direct_answer_node

# 路由函数：读取调度员的决定，告诉图该往哪走
def route_decision(state: AgentState):
    return state["next_step"]


def build_graph():
    workflow = StateGraph(AgentState)

    # 1. 注册所有节点
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("extractor", extractor_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("chatbot", direct_answer_node)  # 注册闲聊节点

    # 2. 起点直达调度员
    workflow.add_edge(START, "supervisor")

    # 3. 动态路由：根据调度员的决定，决定下一步去哪
    workflow.add_conditional_edges(
        "supervisor",
        route_decision,
        {
            "direct_answer": "chatbot",
            "researcher": "researcher",  # 如果决定是 researcher，就去 researcher 节点
            "extractor": "extractor",  # 如果决定是 extractor，就去 extractor 节点
            "both": "researcher"  # 如果决定是 both，先去 researcher
        }
    )

    # chatbot 处理完直接结束
    workflow.add_edge("chatbot", END)

    # 4. 如果走的是 both 路线，researcher 完了之后，必须去 extractor
    # 但由于我们这里分不清是不是 both，所以我们要加个逻辑：
    # 其实在 LangGraph 里，researcher 如果直接连 extractor，那不管前面是 researcher 还是 both，都会去 extractor。
    # 所以我们需要加一个判断。为了简单，我们这里做个小假设：
    # 如果 researcher 跑完了，但是之前决定的是 "researcher"，就直接去 analyst；否则去 extractor。

    # 为了让流程清晰，我们可以这样设计：
    # researcher 结束后，看 state["next_step"] 是什么。如果是 "both"，去 extractor；如果是 "researcher"，直接去 analyst。

    workflow.add_conditional_edges(
        "researcher",
        lambda state: "extractor" if state["next_step"] == "both" else "analyst"
    )

    # extractor 结束后，肯定去 analyst（因为如果是单独 extractor，前面直接就去了；如果是 both，researcher 完了来这，然后去 analyst）
    workflow.add_edge("extractor", "analyst")

    # analyst 结束后，任务完成
    workflow.add_edge("analyst", END)

    return workflow.compile()