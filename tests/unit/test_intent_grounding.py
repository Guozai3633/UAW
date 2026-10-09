"""Exact source grounding handles Unicode and ambiguity without inferred quotes."""

from copy import deepcopy

import pytest

from uaw.intent.semantic import ground_proposal
from uaw.run.inputs import InputSet
from uaw.shared.errors import DomainError


def inputs(text):
    return InputSet(
        {}, {}, ({"kind": "input", "id": "original", "version": "1"},), ({"text": text},)
    )


def proposal(quote):
    return {
        "summary": "理解提示",
        "requirements": [{"quote": quote}],
        "outputs": [],
        "assumptions": [],
        "unresolved": [],
    }


def test_grounding_preserves_original_unicode_whitespace_and_raw_model_proposal():
    source = "😀 前文\r\n不要  发布。 后文"
    raw = proposal({"source_index": 0, "text": "不要  发布。"})
    original = deepcopy(raw)
    result = ground_proposal(raw, inputs(source))
    quote = result["requirements"][0]["quote"]
    assert raw == original and source[quote["start"] : quote["end"]] == quote["text"]
    assert quote["start"] == 6 and quote["end"] == 13


@pytest.mark.parametrize(
    "source,quote,code",
    [
        ("甲甲甲", {"source_index": 0, "text": "甲甲"}, "intent_quote_ambiguous"),
        ("不要  发布", {"source_index": 0, "text": "不要 发布"}, "intent_quote_invalid"),
        ("保留文件", {"source_index": 0, "text": "删除文件"}, "intent_quote_invalid"),
        ("保留文件", {"source_index": 1, "text": "保留文件"}, "intent_quote_invalid"),
        ("保留文件", {"source_index": 0, "text": ""}, "intent_quote_invalid"),
        ("保留文件", {"source_index": 0, "text": "保留文件", "start": 0}, "intent_quote_invalid"),
        (
            "保留文件",
            {"source_index": 0, "text": "保留文件", "start": 1, "end": 4},
            "intent_quote_invalid",
        ),
    ],
)
def test_grounding_rejects_ambiguity_invention_normalization_and_invalid_legacy_span(
    source, quote, code
):
    with pytest.raises(DomainError) as denied:
        ground_proposal(proposal(quote), inputs(source))
    assert denied.value.failure.code == code


def test_grounding_accepts_exact_legacy_span_to_disambiguate_repeated_text():
    quote = {"source_index": 0, "text": "保留", "start": 3, "end": 5}
    raw = proposal(quote)
    assert ground_proposal(raw, inputs("保留，保留")) == raw
