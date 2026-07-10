import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "scan_text.py"
spec = importlib.util.spec_from_file_location("scan_text", MODULE_PATH)
scan_text = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(scan_text)


def test_chatbot_artifact():
    report = scan_text.analyze("Источник: turn0search1 и sandbox:/mnt/data/file.txt")
    markers = {f["marker"] for f in report["findings"]}
    assert "openai_ref" in markers
    assert "sandbox_link" in markers


def test_bureaucratic_marker():
    report = scan_text.analyze("В целях обеспечения качества следует осуществлять проведение проверки.")
    markers = {f["marker"] for f in report["findings"]}
    assert "в целях" in markers
    assert "осуществлять" in markers


def test_clean_text():
    report = scan_text.analyze(
        "Мы проверили отчёт и нашли две ошибки. Первую исправили сразу, вторую вынесли в отдельную задачу."
    )
    assert not any(f["category"] == "artifact" for f in report["findings"])
