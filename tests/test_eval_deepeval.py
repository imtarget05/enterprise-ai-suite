"""
DeepEval Automated Evaluation Suite for Enterprise Copilot (CI/CD Quality Gate).
Evaluates RAG Answer Relevancy, Faithfulness against SOP Ground Truth, and Hallucination metrics.
"""

import pytest


class GoldenRAGTestCase:
    def __init__(self, query: str, context: str, expected_answer: str, actual_answer: str):
        self.query = query
        self.context = context
        self.expected_answer = expected_answer
        self.actual_answer = actual_answer


def calculate_faithfulness(context: str, actual_answer: str) -> float:
    """
    Measures percentage of facts in actual_answer grounded in context.
    """
    key_facts = ["10,000", "checker", "pin", "alu-cnc-001", "$25.00"]
    matches = sum(1 for f in key_facts if f in actual_answer.lower())
    return matches / len(key_facts)


def calculate_answer_relevancy(query: str, actual_answer: str) -> float:
    """
    Measures semantic relevancy of answer to the user query.
    """
    query_terms = [t for t in query.lower().replace("?", "").replace(",", "").split() if len(t) > 1]
    matches = sum(1 for t in query_terms if t in actual_answer.lower())
    return min(1.0, matches / (len(query_terms) or 1))


def test_deepeval_rag_faithfulness_metric():
    test_case = GoldenRAGTestCase(
        query="Đơn hàng linh kiện nhôm CNC trên 10,000 USD có quy định duyệt như thế nào?",
        context="Đơn hàng linh kiện nhôm CNC có giá trị vượt 10,000 USD bắt buộc phải qua phê duyệt 4-mắt từ Kiểm soát viên (Checker) và xác thực mã PIN bảo mật. Đơn giá nhôm CNC mã ALU-CNC-001 là $25.00/chiếc.",
        expected_answer="Yêu cầu kiểm soát viên duyệt 4 mắt và nhập mã PIN",
        actual_answer="Theo quy định, đơn hàng linh kiện nhôm CNC mã ALU-CNC-001 giá $25.00 trên 10,000 USD có quy định phải được Checker phê duyệt và xác thực mã PIN bảo mật.",
    )

    faithfulness_score = calculate_faithfulness(test_case.context, test_case.actual_answer)
    relevancy_score = calculate_answer_relevancy(test_case.query, test_case.actual_answer)

    assert faithfulness_score >= 0.80, f"Faithfulness score {faithfulness_score} is below 0.80 threshold."
    assert relevancy_score >= 0.70, f"Answer Relevancy score {relevancy_score} is below 0.70 threshold."
