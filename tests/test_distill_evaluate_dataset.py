import unittest
from distill.scripts.evaluate_dataset import field_map, finding_keys, score_gold


class EvaluationTests(unittest.TestCase):
    def test_field_map_normalizes_values(self):
        answer = {"fields": [{"name": " 合同金额 ", "value": "100", "status": "已提取"}]}
        self.assertEqual(field_map(answer), {"合同金额": ("100", "已提取")})

    def test_finding_keys(self):
        self.assertEqual(finding_keys({"findings": [{"category": "付款风险", "severity": "高"}]}), {("付款风险", "高")})

    def test_gold_score(self):
        answer = {"fields": [{"name": "金额", "value": "100", "status": "已提取"}],
                  "findings": [{"category": "付款风险", "severity": "高"}]}
        result = score_gold([{"project_id": "P1", "answer": answer}], [{"project_id": "P1", "answer": answer}])
        self.assertEqual(result["field_exact_match_accuracy"], 1.0)
        self.assertEqual(result["finding_category_severity_f1"], 1.0)


if __name__ == "__main__":
    unittest.main()
