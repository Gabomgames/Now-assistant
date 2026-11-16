import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from validate_dataset import check_file

class DataTests(unittest.TestCase):
    def test_original_seed_valid(self):
        path=Path(__file__).resolve().parents[1]/"data/now_seed.jsonl"
        count,errors=check_file(path)
        self.assertGreaterEqual(count,20)
        self.assertEqual([],errors)
    def test_duplicate_prompt_rejected(self):
        record={'prompt':[{'role':'user','content':'Oi'}],'completion':[{'role':'assistant','content':'Olá'}]}
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'test.jsonl'
            path.write_text(json.dumps(record)+'\n'+json.dumps(record)+'\n',encoding='utf-8')
            _,errors=check_file(path)
            self.assertTrue(any('duplicate' in e for e in errors))
    def test_empty_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'empty.jsonl';path.write_text('',encoding='utf-8')
            _,errors=check_file(path)
            self.assertIn('empty dataset',errors)
    def test_eval_has_unique_ids(self):
        path=Path(__file__).resolve().parents[1]/"data/eval_cases.jsonl"
        rows=[json.loads(x) for x in path.read_text(encoding='utf-8').splitlines()]
        ids=[x['id'] for x in rows]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertGreaterEqual(len(ids),10)
if __name__=='__main__':unittest.main()
