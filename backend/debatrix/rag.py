import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "corpus"
TOKEN = re.compile(r"[a-z0-9]+")
# Function words carry no topical signal; without this, "Should ... the ..." in a motion
# matches passages from unrelated topics.
STOPWORDS = frozenset(
    "a an and are as at be by can could do does for from give has have how i if in into is it "
    "its me my not of on or our should so than that the their them then there these they this "
    "to was we were what when which who will with would you your".split()
)
# Keep only hits scoring at least this fraction of the best hit.
RELATIVE_CUTOFF = 0.4


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN.findall(text.lower()) if t not in STOPWORDS]


class BM25:
    def __init__(self, docs: list[dict[str, object]]) -> None:
        self.docs = docs
        self.tokens = [tokenize(d["text"] + " " + d["title"]) for d in docs]
        self.avg = sum(map(len, self.tokens)) / max(1, len(self.tokens))
        self.df = {}
        for ts in self.tokens:
            for w in set(ts):
                self.df[w] = self.df.get(w, 0) + 1

    def search(self, q: str, k: int = 4) -> list[dict[str, object]]:
        terms = tokenize(q)
        n = len(self.docs)
        scores = []
        for i, ts in enumerate(self.tokens):
            freq = {w: ts.count(w) for w in set(terms)}
            score = 0
            for w, tf in freq.items():
                if tf:
                    idf = math.log(1 + (n - self.df.get(w, 0) + 0.5) / (self.df.get(w, 0) + 0.5))
                    score += (
                        idf * tf * 2.2 / (tf + 1.2 * (0.25 + 0.75 * len(ts) / max(1, self.avg)))
                    )
            scores.append((score, i))
        ranked = sorted(scores, reverse=True)
        best = ranked[0][0] if ranked else 0
        if best <= 0:
            return []
        hits = [(s, i) for s, i in ranked[:k] if s >= best * RELATIVE_CUTOFF]
        return [dict(self.docs[i], score=round(s, 4), id=n + 1) for n, (s, i) in enumerate(hits)]


def load_corpus() -> list[dict[str, object]]:
    docs = []
    for p in ROOT.glob("*.md"):
        raw = p.read_text(encoding="utf-8-sig", errors="replace")
        lines = raw.splitlines()
        title = lines[0].lstrip("# ").strip()
        for block in re.split(r"\n\s*\n", "\n".join(lines[1:])):
            sources = re.findall(r"https?://\S+", block)
            passage = " ".join(
                line.strip()
                for line in block.splitlines()
                if line.strip() and not line.strip().startswith("http")
            )
            if passage:
                docs.append(
                    {
                        "title": title,
                        "source": sources[0] if sources else "",
                        "sources": sources,
                        "text": passage,
                    }
                )
    return docs


CORPUS = load_corpus()
INDEX = BM25(CORPUS)

# One pseudo-document per corpus file, used to decide which topic a motion belongs to.
_TOPICS: dict[str, list[dict[str, object]]] = {}
for _doc in CORPUS:
    _TOPICS.setdefault(str(_doc["title"]), []).append(_doc)
TOPIC_INDEX = BM25(
    [
        {"title": title, "text": " ".join(str(d["text"]) for d in docs)}
        for title, docs in _TOPICS.items()
    ]
)
_TOPIC_PASSAGES = {title: BM25(docs) for title, docs in _TOPICS.items()}


def match_topic(motion: str) -> str | None:
    """Corpus topic a motion belongs to, or None for a custom motion outside the corpus."""
    hits = TOPIC_INDEX.search(motion, 2)
    if not hits:
        return None
    # Require a clear winner so a vague custom motion doesn't borrow an unrelated topic.
    if len(hits) > 1 and hits[1]["score"] > 0.8 * hits[0]["score"]:
        return None
    return str(hits[0]["title"])


def retrieve(query: str, k: int = 4, motion: str | None = None) -> list[dict[str, object]]:
    """Two-stage retrieval: pick the motion's topic, then rank its passages by the query.

    Without a recognised topic it falls back to searching the whole corpus.
    """
    topic = match_topic(motion) if motion else None
    if topic is None:
        return INDEX.search(query, k)
    index = _TOPIC_PASSAGES[topic]
    return index.search(query, k) or index.search(motion or "", k)
