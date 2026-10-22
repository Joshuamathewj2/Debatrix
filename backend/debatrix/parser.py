import re

MARKER = re.compile(r"@@(POSITION|ARGUMENTS|COUNTER|QUESTION)@@")
PREFIXES = [
    m[:i]
    for name in ("POSITION", "ARGUMENTS", "COUNTER", "QUESTION")
    for m in ("@@" + name + "@@",)
    for i in range(1, len(m))
]


class SectionParser:
    def __init__(self) -> None:
        self.buffer = ""
        self.section = None
        self.sections = {}

    def feed(self, chunk: str) -> list[dict[str, str]]:
        self.buffer += chunk
        events = []
        while True:
            m = MARKER.search(self.buffer)
            if m:
                before = self.buffer[: m.start()]
                if before and self.section:
                    self._add(before)
                    events.append({"type": "section", "section": self.section, "text": before})
                self.section = m.group(1).lower()
                self.buffer = self.buffer[m.end() :]
                continue
            keep = max((len(p) for p in PREFIXES if self.buffer.endswith(p)), default=0)
            safe = self.buffer[:-keep] if keep else self.buffer
            self.buffer = self.buffer[len(safe) :]
            if safe and self.section:
                self._add(safe)
                events.append({"type": "section", "section": self.section, "text": safe})
            break
        return events

    def finish(self) -> dict[str, str]:
        if self.buffer and self.section:
            self._add(self.buffer)
        self.buffer = ""
        return self.sections

    def _add(self, value: str) -> None:
        self.sections[self.section] = self.sections.get(self.section, "") + value
