import re

import pytest

from debatrix.debate_engine import stance_drift
from debatrix.fallacies import RULES, detect
from debatrix.parser import SectionParser
from debatrix.rag import BM25, INDEX


def test_bm25():
    idx = BM25(
        [
            {"title": "AI regulation", "text": "govern AI risk"},
            {"title": "uniforms", "text": "school clothes"},
        ]
    )
    assert idx.search("AI risk")[0]["title"] == "AI regulation"
    assert 25 <= len(INDEX.docs) <= 40
    assert all(doc["source"].startswith("https://") for doc in INDEX.docs)


def test_parser_split_marker():
    p = SectionParser()
    for chunk in [
        "@@POS",
        "ITION@@Firm\n@@ARGU",
        "MENTS@@Evidence",
        "@@COUN",
        "TER@@Reply@@QUESTION@@Ask",
    ]:
        p.feed(chunk)
    out = p.finish()
    assert (
        out["position"] == "Firm\n"
        and out["arguments"] == "Evidence"
        and out["counter"] == "Reply"
        and out["question"] == "Ask"
    )


def test_fallacies_spans():
    text = "Everyone knows it; what about the other side?"
    matches = detect(text)
    assert {m["type"] for m in matches} >= {"Bandwagon", "Whataboutism"}
    assert all(text[m["start"] : m["end"]] == m["text"] for m in matches)


def test_stance_drift():
    assert not stance_drift("@@POSITION@@I argue against AI regulation.", "AGAINST")
    assert stance_drift("@@POSITION@@I agree with your FOR position.", "AGAINST")


@pytest.mark.parametrize("query", ["", "unknownxyz"])
def test_bm25_empty_or_unknown_query_returns_no_results(query):
    index = BM25([{"title": "AI", "text": "regulation and safety"}])
    assert index.search(query) == []


def test_bm25_relevant_document_ranks_first():
    index = BM25(
        [
            {"title": "AI policy", "text": "govern artificial intelligence risk"},
            {"title": "School uniforms", "text": "clothing rules for students"},
        ]
    )
    assert index.search("artificial intelligence risk")[0]["title"] == "AI policy"


@pytest.mark.parametrize("name,pattern,_", RULES)
def test_each_fallacy_is_detected_with_exact_span(name, pattern, _):
    match = re.search(
        pattern,
        {
            "Ad hominem": "That idiot ignores evidence.",
            "Straw man": "So you're saying we should ban everything.",
            "Slippery slope": "This will lead to chaos.",
            "False dilemma": "Either we act now or we lose.",
            "Appeal to authority": "The expert says it is safe.",
            "Hasty generalization": "All students are careless.",
            "Whataboutism": "What about the other policy?",
            "Appeal to emotion": "If you care about people, agree.",
            "Bandwagon": "Everyone knows the answer.",
            "Circular reasoning": "It is true because it is true.",
        }[name],
        re.I,
    )
    assert match is not None
    sample = match.string
    result = next(item for item in detect(sample) if item["type"] == name)
    assert sample[result["start"] : result["end"]] == result["text"] == match.group()


def test_neutral_argument_has_no_fallacy_matches():
    assert detect("The proposal costs $5 million and would run for two years.") == []


@pytest.mark.parametrize("marker", ["POSITION", "ARGUMENTS", "COUNTER", "QUESTION"])
def test_parser_handles_marker_at_every_chunk_boundary(marker):
    next_marker = "COUNTER" if marker == "QUESTION" else "QUESTION"
    source = f"@@{marker}@@A\n@@{next_marker}@@B"
    marker_text = f"@@{marker}@@"
    start = source.index(marker_text)
    for boundary in range(start + 1, start + len(marker_text)):
        parser = SectionParser()
        parser.feed(source[:boundary])
        parser.feed(source[boundary:])
        sections = parser.finish()
        assert sections[marker.lower()] == "A\n"
        assert sections[next_marker.lower()] == "B"


@pytest.mark.parametrize(
    "text,expected",
    [
        ("@@POSITION@@I argue AGAINST the policy.", False),
        ("@@POSITION@@I now agree with your case.", True),
        ("@@POSITION@@You are right about this.", True),
    ],
)
def test_stance_drift_cases(text, expected):
    assert stance_drift(text, "AGAINST") is expected


@pytest.mark.parametrize(
    "text",
    [
        "@@POSITION@@Regulation would therefore stifle innovation.",
        "@@POSITION@@This policy is bad for workers and for small firms.",
        "@@POSITION@@Before we accept it, look at the information we have.",
    ],
)
def test_ordinary_use_of_for_is_not_drift(text):
    # Regression: a substring check flagged "therefore"/"for workers" as taking the FOR side.
    assert stance_drift(text, "AGAINST") is False


def test_explicit_flip_is_drift_on_both_sides():
    assert stance_drift("@@POSITION@@I argue in favour of the policy.", "AGAINST")
    assert stance_drift("@@POSITION@@I now oppose this policy.", "FOR")
    assert not stance_drift("@@POSITION@@I argue for this policy.", "FOR")


def test_retrieval_stays_on_topic():
    from debatrix.rag import retrieve

    motion = "Should AI development be regulated?"
    # Regression: words like "harm"/"systems" used to pull in teen social media and energy passages.
    hits = retrieve(f"{motion} biased hiring tools and deepfakes cause harm", 3, motion=motion)
    assert hits
    assert {h["title"] for h in hits} == {"Governing Artificial Intelligence"}


@pytest.mark.parametrize(
    "motion,topic",
    [
        ("Should AI development be regulated?", "Governing Artificial Intelligence"),
        ("Should governments provide universal basic income?", "Basic Income Evidence"),
        ("Should nuclear energy be expanded?", "Nuclear Energy and Climate"),
        (
            "Should social media access be restricted for teens?",
            "Social Media and Adolescent Wellbeing",
        ),
        ("Is remote work better than office work?", "Remote Work Research"),
        ("Should schools require uniforms?", "School Uniform Evidence"),
        ("Should pineapple go on pizza?", None),
    ],
)
def test_motion_maps_to_topic(motion, topic):
    from debatrix.rag import match_topic

    assert match_topic(motion) == topic


def test_mock_varies_with_user_point_and_uses_evidence():
    from debatrix.llm.providers import MockProvider

    evidence = [{"title": "T", "source": "s", "text": "Costs fell 40% in pilots. More text."}]

    def run(point: str) -> str:
        return "".join(
            MockProvider().stream("Should X be banned?", "for", "Socratic", point, evidence)
        )

    first, second = run("Bans always work."), run("Look at the 2019 data on enforcement.")
    assert first != second
    assert "Costs fell 40% in pilots [1]" in first
    assert "Should X be banned?:" not in first  # motion is quoted, not spliced into a sentence
    assert "Give your opening argument" not in run("Give your opening argument.")


def test_judge_ignores_opening_prompt():
    from debatrix.judge import OPENING_PROMPT, score_debate

    opening = {"argument": OPENING_PROMPT, "fallacies": []}
    real = {"argument": "However, according to the 2023 data, costs fell 40%.", "fallacies": []}
    assert score_debate([opening, real]) == score_debate([real])


def test_drift_retries_same_provider_before_mock():
    from debatrix.debate_engine import stream_turn

    class FlakyProvider:
        name = "flaky"

        def __init__(self):
            self.calls = 0

        def stream(self, *args):
            self.calls += 1
            if self.calls == 1:
                yield "@@POSITION@@I agree with you.@@ARGUMENTS@@x"
            else:
                yield "@@POSITION@@I argue against it.@@ARGUMENTS@@Costs.@@COUNTER@@No.@@QUESTION@@Why?"

    provider = FlakyProvider()
    events = list(stream_turn(provider, "topic", "for", "Socratic", "point", []))
    done = events[-1]
    assert provider.calls == 2
    assert done["provider"] == "flaky"
    assert "against" in done["sections"]["position"]
