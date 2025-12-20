import re
from typing import List

from .pdf_loader import Page
from .toc_parser import TocItem

# ---------------------------------------------------------------------
# Numeric hierarchical headings
# Matches:
#   1 Introduction
#   11.2 Dealing with frequent dishonor of inward clearing cheques
#   11.3.1 Charges for dishonor of cheques
#
# Rejects:
#   2010
#   (a) Procedure ...
# ---------------------------------------------------------------------
NUM_HEADING = re.compile(
    r"""^
    \s*
    (?!\(?[a-zA-Z]\))          # reject clause markers like (a), (b)
    (?!\d{4}\b)                # reject years like 2010
    (\d+(?:\.\d+)+|\d+)        # 1 | 1.2 | 11.3.1
    \s+
    ([A-Za-z].{10,200})        # title must start with a letter, reasonable length
    $
    """,
    re.VERBOSE,
)

# ---------------------------------------------------------------------
# ALL CAPS headings
# Matches:
#   DEFINITIONS
#   ANNEXURE – I
#   GENERAL GUIDELINES
# ---------------------------------------------------------------------
ALLCAPS = re.compile(
    r"^\s*([A-Z][A-Z0-9 \-/,&()]{6,120})\s*$"
)

# ---------------------------------------------------------------------
# Lines that should NEVER be treated as headings
# (headers, footers, running titles)
# ---------------------------------------------------------------------
LOW_SIGNAL_PHRASES = [
    "table of contents",
    "cheque collection policy",
    "page |",
    "page|",
    "version",
    "policy",
]


def detect_headings(pages: List[Page]) -> List[TocItem]:
    """
    Detect structural headings from PDF text when TOC is missing or unreliable.

    Rules:
    - Prefer numeric hierarchical headings (1, 1.2, 11.3.1)
    - Reject years, clauses, headers/footers
    - Accept ALL-CAPS headings as level-1
    - De-duplicate near-identical headings
    """

    items: List[TocItem] = []

    for p in pages:
        for raw_line in (p.text or "").splitlines():
            line = raw_line.strip()
            if not line:
                continue

            lower = line.lower()

            # ---------------------------------------------------------
            # Filter obvious noise (headers / footers)
            # ---------------------------------------------------------
            if any(ph in lower for ph in LOW_SIGNAL_PHRASES):
                continue

            # ---------------------------------------------------------
            # Numeric hierarchical headings
            # ---------------------------------------------------------
            m = NUM_HEADING.match(line)
            if m:
                num, title = m.group(1), m.group(2).strip()

                # Extra guard: reject clause-like titles
                if title.startswith("(") and title[1:2].isalpha():
                    continue

                level = num.count(".") + 1
                items.append(
                    TocItem(
                        level=level,
                        title=title,
                        start_page=p.page_num,
                        number=num,
                    )
                )
                continue

            # ---------------------------------------------------------
            # ALL CAPS headings (fallback)
            # ---------------------------------------------------------
            m2 = ALLCAPS.match(line)
            if m2:
                title = m2.group(1).strip()

                if "TABLE OF CONTENTS" in title:
                    continue

                items.append(
                    TocItem(
                        level=1,
                        title=title,
                        start_page=p.page_num,
                        number=None,
                    )
                )

    # -----------------------------------------------------------------
    # De-duplicate near-identical headings
    # -----------------------------------------------------------------
    uniq: List[TocItem] = []
    seen = set()

    for it in items:
        key = (it.title.lower(), it.start_page, it.level)
        if key not in seen:
            uniq.append(it)
            seen.add(key)

    return uniq
