import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

@dataclass
class TocItem:
    level: int               # 1=chapter/major section, 2=subsection...
    title: str
    start_page: int
    number: Optional[str] = None

_TOC_LINE = re.compile(r"^\s*(?:(\d+(?:\.\d+)*)\s+)?(.+?)\s+(\d+)\s*$")

def parse_toc_from_text(toc_text: str) -> List[TocItem]:
    items: List[TocItem] = []
    for line in toc_text.splitlines():
        m = _TOC_LINE.match(line.strip())
        if not m:
            continue
        num, title, page = m.group(1), m.group(2).strip(), int(m.group(3))
        # Infer level from numbering depth; fallback to level 1
        level = (num.count(".") + 1) if num else 1
        items.append(TocItem(level=level, title=title, start_page=page, number=num))
    return items
