# src/rag_starterkit/ingest/leaf_chunker.py
#
# Full drop-in replacement.
# Purpose:
# - Leaf-first chunking (only chunk leaf nodes; parents with children are not chunked)
# - Preserve natural hierarchy order using order_key
# - Avoid duplicate title_path / number_path entries (common when TOC + heading fallback overlap)
# - Add section-aware metadata (section_type, policy_topic)
# - Table-aware behavior: keep tables as single chunks (prevents fragmented annexures)

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from .pdf_loader import Page
from .hierarchy_builder import Node


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    source_path: str
    title_path: List[str]
    number_path: List[str]
    page_start: int
    page_end: int
    order_key: str
    text: str
    metadata: Dict


def _hash_id(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()[:16]

def _clean_body_text(text: str, title: str) -> str:
    lines = []
    for l in text.splitlines():
        ll = l.strip().lower()
        if not l.strip():
            continue
        if title.lower() in ll:
            continue
        if re.match(r"^\s*\d+(?:\.\d+)*\s+", l):
            continue
        if "page |" in ll or "version" in ll or "cheque collection policy" in ll:
            continue
        lines.append(l)
    return "\n".join(lines).strip()

def _push_unique(stack: List[str], value: str) -> List[str]:
    """Avoid consecutive duplicates in hierarchy stacks."""
    if not value:
        return stack
    return stack if (stack and stack[-1] == value) else (stack + [value])


def _get_text_between(pages: List[Page], start_page: int, end_page: int) -> str:
    parts: List[str] = []
    for p in pages:
        if start_page <= p.page_num <= end_page:
            parts.append(p.text or "")
    return "\n".join(parts).strip()


_TABLE_HINT_RE = re.compile(r"(\bS\.?No\.?\b|\bAnnexure\b|\bSr\.?No\.?\b)", flags=re.IGNORECASE)


def _looks_like_table(text: str) -> bool:
    """
    Heuristic: many short lines with repeated spacing/columns, pipes, or serial numbers.
    This avoids splitting annexure/tables into many chunks.
    """
    if not text:
        return False
    lines = [l for l in text.splitlines() if l.strip()]
    if len(lines) < 8:
        return False

    pipe_lines = sum(1 for l in lines if "|" in l)
    multi_space_lines = sum(1 for l in lines if re.search(r"\s{3,}", l))
    numeric_start_lines = sum(1 for l in lines if re.match(r"^\s*\d{1,3}\s+[\w(]", l))

    # If it's an annexure/table-ish region, be more permissive
    hint = bool(_TABLE_HINT_RE.search(text))

    score = pipe_lines + multi_space_lines + numeric_start_lines
    if hint and score >= 8:
        return True
    return score >= 12


def _policy_topic_from_title(title: str) -> Optional[str]:
    t = (title or "").lower()
    # Extend this mapping over time as your corpus grows
    if "dishonour" in t or "dishonor" in t or "dishonoured" in t or "dishonored" in t:
        return "dishonour"
    if "cts" in t or "cheque truncation" in t:
        return "cts"
    if "positive pay" in t or "pps" in t:
        return "pps"
    if "outstation" in t:
        return "outstation"
    if "immediate credit" in t:
        return "immediate_credit"
    if "return" in t and "cheque" in t:
        return "return_of_cheque"
    return None


def leaf_chunks_from_tree(
    pages: List[Page],
    doc_id: str,
    source_path: str,
    root: Node,
    doc_last_page: int,
    max_chars: int = 2200,
    min_chars: int = 200,
) -> List[Chunk]:
    """
    Builds leaf-only chunks from a hierarchy tree.

    Rules:
    - If node has children: do NOT chunk parent; chunk children.
    - If leaf node: chunk (title + content).
    - If leaf content > max_chars: split into sequential parts (except tables/annexures).
    - Always preserve natural order using order_key.
    """

    # Ensure all end_page fields are filled
    def fill_end_pages(n: Node):
        if n.end_page is None:
            n.end_page = doc_last_page
        for ch in n.children:
            if ch.end_page is None:
                ch.end_page = doc_last_page
            fill_end_pages(ch)

    fill_end_pages(root)

    out: List[Chunk] = []

    def walk(node: Node, title_stack: List[str], num_stack: List[str]):
        # Parent nodes are not chunked if they have children
        if node.children:
            for ch in node.children:
                # Push unique to prevent duplicates
                next_titles = _push_unique(title_stack, ch.title)
                next_nums = _push_unique(num_stack, ch.number or "")
                walk(ch, next_titles, next_nums)
            return

        # Leaf node
        leaf_title = (node.title or "").strip() or "Untitled"
        start_p = node.start_page
        end_p = max(node.start_page, node.end_page or node.start_page)

        raw = _get_text_between(pages, start_p, end_p)
        clean_raw = _clean_body_text(raw, leaf_title)
        base = f"{leaf_title}\n{clean_raw}".strip()


        # Build chunk text as "Title + Content"
        base = f"{leaf_title}\n{raw}".strip()

        # Keep very small leaves (do not drop); but ensure we still include title
        if len(base) < min_chars:
            base = base

        is_annexure = "annexure" in leaf_title.lower()
        is_table = _looks_like_table(base)

        # # Split logic: avoid splitting tables/annexures
        # if (len(base) <= max_chars) or is_table or is_annexure:
        #     chunk_texts = [base]
        # else:
        #     chunk_texts = []
        #     cursor = 0
        #     while cursor < len(base):
        #         chunk_texts.append(base[cursor : cursor + max_chars])
        #         cursor += max_chars
        # If this is a numbered policy section, keep ONE chunk per section
        if node.number:
            chunk_texts = [base]

        # Tables / annexures should also remain single chunks
        elif is_table or is_annexure or len(base) <= max_chars:
            chunk_texts = [base]

        # Fallback: split only for unnumbered, very long text
        else:
            chunk_texts = []
            cursor = 0
            while cursor < len(base):
                chunk_texts.append(base[cursor : cursor + max_chars])
                cursor += max_chars

        # Final stacks: ensure leaf title appears once
        final_title_path = _push_unique(title_stack, leaf_title)
        final_num_path = num_stack[:]
        if node.number:
            final_num_path = _push_unique(final_num_path, node.number)

        # Section-level metadata (bank/version should be added later in ingest_pipeline.py)
        section_meta = {
            "section_type": "annexure" if is_annexure else "policy",
            "policy_topic": _policy_topic_from_title(leaf_title),
        }

        for idx, ct in enumerate(chunk_texts, start=1):
            order_key = f"{start_p:04d}-0000-{idx:04d}"
            hid = _hash_id(f"{doc_id}|{'/'.join(final_title_path)}|{start_p}-{end_p}|{idx}")

            meta = {
                "doc_id": doc_id,
                "source_path": source_path,
                "page_start": start_p,
                "page_end": end_p,
                "order_key": order_key,
                "title_path": final_title_path,
                "number_path": final_num_path,
                **section_meta,
            }

            out.append(
                Chunk(
                    chunk_id=f"{doc_id}:{hid}",
                    doc_id=doc_id,
                    source_path=source_path,
                    title_path=final_title_path,
                    number_path=final_num_path,
                    page_start=start_p,
                    page_end=end_p,
                    order_key=order_key,
                    text=ct,
                    metadata=meta,
                )
            )

    # Start from root children (skip ROOT label)
    for ch in root.children:
        walk(ch, _push_unique([], ch.title), _push_unique([], ch.number or ""))

    # Ensure strict natural ordering
    out.sort(key=lambda c: c.order_key)
    return out
