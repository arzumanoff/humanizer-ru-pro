#!/usr/bin/env python3
"""Лёгкий детерминированный аудит русского текста.

Сканер не определяет авторство и не обещает «обход детекторов».
Он подсвечивает формальные артефакты, канцелярские маркеры и ритм.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path
from typing import Any

ARTIFACTS = {
    "openai_ref": r"\bturn\d+(?:search|file|image|news|video|ref)\d+\b",
    "oai_citation": r":contentReference\[oaicite:[^\]]+\]|oai_citation:[^\s]+|citeturn\d+file\d+",
    "sandbox_link": r"sandbox:/mnt/data/[^\s)]+",
    "grok_artifact": r"grok_card://|<grok-card\b|grok_render_citation_card_json",
    "gemini_citation": r"\[cite_start\]|\[cite:\s*\d+(?:\s*,\s*\d+)*\]",
    "placeholder_url": r"\b(?:INSERT_SOURCE_URL|URL_HERE|PASTE_[A-Z_]*URL_HERE)\b",
    "writing_block": r":::writing\{[^}]*\}",
    "zero_width": r"[\u200b-\u200f\u2060\ufeff]",
}

BUREAUCRATIC = {
    "осуществлять": r"\bосуществля(?:ть|ет|ют|ется|ются|лся|лась|лось|лись)\b",
    "производить": r"\bпроизводи(?:ть|т|л[аио]?|ли)\b",
    "имеется возможность": r"\bимеется возможность\b",
    "в целях": r"\bв целях\b",
    "данный": r"\bданн(?:ый|ая|ое|ые|ого|ой|ому|ым|ыми|ых)\b",
    "является": r"\bявля(?:ется|ются|лся|лась|лось|лись)\b",
    "следует отметить": r"\bследует отметить\b",
    "важно отметить": r"\bважно отметить\b",
    "стоит подчеркнуть": r"\bстоит подчеркнуть\b",
    "таким образом": r"\bтаким образом\b",
    "в заключение": r"\bв заключение\b",
}

VAGUE = {
    "многие": r"\bмногие (?:эксперты|специалисты|пользователи|исследователи)\b",
    "исследования показывают": r"\bисследования показывают\b",
    "эксперты считают": r"\bэксперты считают\b",
    "ключевая роль": r"\b(?:ключевую|важную) роль\b",
    "огромное значение": r"\bогромное значение\b",
    "новая эра": r"\bновую эру\b",
}


def read_text(source: str) -> str:
    if source == "-":
        return sys.stdin.read()
    return Path(source).read_text(encoding="utf-8")


def positions(text: str, pattern: str) -> list[int]:
    return [m.start() for m in re.finditer(pattern, text, flags=re.I | re.M)]


def line_numbers(text: str, offsets: list[int]) -> list[int]:
    return sorted({text.count("\n", 0, p) + 1 for p in offsets})


def split_sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?…])\s+(?=[А-ЯЁA-Z0-9«„“\"(])", text.strip())
    return [c.strip() for c in chunks if c.strip()]


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-zА-Яа-яЁё0-9-]+", text))


def analyze(text: str) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []

    for category, mapping in (
        ("artifact", ARTIFACTS),
        ("bureaucratic", BUREAUCRATIC),
        ("vague", VAGUE),
    ):
        for name, pattern in mapping.items():
            pos = positions(text, pattern)
            if pos:
                findings.append({
                    "category": category,
                    "marker": name,
                    "count": len(pos),
                    "lines": line_numbers(text, pos),
                })

    sentences = split_sentences(text)
    lengths = [word_count(s) for s in sentences]
    mean_len = statistics.mean(lengths) if lengths else 0.0
    stdev = statistics.pstdev(lengths) if len(lengths) > 1 else 0.0
    cv = stdev / mean_len if mean_len else 0.0

    em_dashes = text.count("—")
    artifact_count = sum(f["count"] for f in findings if f["category"] == "artifact")
    style_count = sum(f["count"] for f in findings if f["category"] != "artifact")

    score = 100
    score -= min(40, artifact_count * 15)
    score -= min(30, style_count * 3)
    if len(sentences) >= 5 and cv < 0.22:
        score -= 8
    if word_count(text) and em_dashes / max(1, word_count(text)) > 0.025:
        score -= 5
    score = max(0, score)

    return {
        "words": word_count(text),
        "sentences": len(sentences),
        "sentence_length": {
            "mean": round(mean_len, 2),
            "min": min(lengths) if lengths else 0,
            "max": max(lengths) if lengths else 0,
            "cv": round(cv, 3),
        },
        "typography": {
            "em_dashes": em_dashes,
            "questions": text.count("?"),
            "exclamations": text.count("!"),
            "headings": len(re.findall(r"(?m)^#{1,6}\s+", text)),
            "bullets": len(re.findall(r"(?m)^\s*[-*•]\s+", text)),
        },
        "findings": findings,
        "editorial_score": score,
        "note": "Оценка редакционная, а не вероятность машинного авторства.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Аудит русского текста")
    parser.add_argument("source", help="UTF-8 файл или '-' для stdin")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        text = read_text(args.source)
    except (OSError, UnicodeError) as exc:
        print(f"Ошибка чтения: {exc}", file=sys.stderr)
        return 2

    report = analyze(text)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if any(f["category"] == "artifact" for f in report["findings"]) else 0

    print("=== Humanizer RU Pro: аудит ===")
    print(f"Слов: {report['words']}; предложений: {report['sentences']}")
    sl = report["sentence_length"]
    print(f"Длина предложений: средняя {sl['mean']}, min {sl['min']}, max {sl['max']}, CV {sl['cv']}")
    print(f"Редакционная оценка: {report['editorial_score']}/100")
    print(report["note"])
    print()

    if not report["findings"]:
        print("Формальные маркеры не найдены.")
        return 0

    for item in report["findings"]:
        lines = ", ".join(map(str, item["lines"][:6]))
        print(f"- [{item['category']}] {item['marker']}: {item['count']} (строки {lines})")

    return 1 if any(f["category"] == "artifact" for f in report["findings"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
