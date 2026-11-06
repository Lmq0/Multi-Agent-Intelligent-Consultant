from workflow.graph import build_graph
from core.log import logger

if __name__ == "__main__":
    app = build_graph()

    test_cases = [
        "你好呀，你是谁？",  # 测试兜底
        "最近有什么影响计算机专业留学生签证的重大新闻？",  # 测试联网
        "我 PDF 里写的 50000 新币学费，现在折合人民币多少钱？"  # 测试综合
    ]

    for i, query in enumerate(test_cases):
        logger.info(f"\n{'=' * 50}\n>>> 测试 {i + 1}：{query}\n{'=' * 50}")
        result = app.invoke({"topic": query})
        logger.info(f"📊 最终输出：\n{result.get('final_advice')}")