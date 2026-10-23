import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import contract_agent as agent

class AgentUtilityTests(unittest.TestCase):
    def test_phone_redacted_before_remote_call(self):
        text = agent.redact_for_remote('联系电话：13812345678')
        self.assertNotIn('13812345678', text)
        self.assertIn('****', text)

    def test_id_redacted_before_remote_call(self):
        text = agent.redact_for_remote('身份证号：110101199001011234')
        self.assertNotIn('110101199001011234', text)
        self.assertIn('*', text)

    def test_text_chunks_preserve_all_content(self):
        original = '合同条款\n' * 12000
        parts = agent.split_chunks(original, 1000)
        self.assertEqual(''.join(parts), original)
        self.assertGreater(len(parts), 1)

    def test_dedupe_removes_exact_duplicate_findings(self):
        item = {'type': '金额矛盾', 'evidence': '金额为100元', 'location': '第2页', 'reason': '总价不一致'}
        self.assertEqual(len(agent.dedupe([item, item.copy()])), 1)

    def test_txt_read_preserves_line_numbers(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'sample.txt'
            p.write_text('第一条\n第二条', encoding='utf-8')
            text, visual_pages = agent.read_document(p)
            self.assertIn('[第1行] 第一条', text)
            self.assertIn('[第2行] 第二条', text)
            self.assertEqual(visual_pages, [])

if __name__ == '__main__':
    unittest.main()
