"""Tests for the detection rules and the scoring harness.

Run from the backend/ directory: `pytest`
"""
from app.detectors import get_engine
from app.eval.dataset import load_samples
from app.eval.metrics import score


def find(code, engine="ast"):
    return {(f.rule_id, f.line) for f in get_engine(engine).analyze(code)}


def test_detects_sql_injection_fstring():
    assert ("PY-SQL-001", 1) in find('cur.execute(f"SELECT {x}")')


def test_detects_eval():
    assert ("PY-EVAL-001", 1) in find("eval(user_input)")


def test_detects_hardcoded_secret():
    assert ("PY-SECRET-001", 1) in find('password = "hunter2"')


def test_ignores_eval_inside_a_string():
    # The AST engine must NOT flag text that only appears in a literal.
    assert find('msg = "call eval() carefully"') == set()


def test_ignores_safe_yaml_loader():
    assert find("yaml.load(t, Loader=yaml.SafeLoader)") == set()


def test_parameterized_query_is_clean():
    assert find('cur.execute("SELECT * FROM u WHERE id = ?", (uid,))') == set()


def test_regex_baseline_false_positives_on_comment():
    # The baseline SHOULD over-fire here — that's the gap the AST engine closes.
    assert find("# remember to call eval() here", engine="regex")
    assert find("# remember to call eval() here", engine="ast") == set()


def test_ast_beats_regex_on_precision():
    samples = load_samples()
    ast_p = score(samples, get_engine("ast")).precision
    regex_p = score(samples, get_engine("regex")).precision
    assert ast_p > regex_p


def test_dataset_loads_with_ground_truth():
    samples = load_samples()
    assert len(samples) >= 20
    assert any(s.expected for s in samples)   # has labeled vulnerabilities
    assert any(s.is_clean for s in samples)   # has clean samples too
