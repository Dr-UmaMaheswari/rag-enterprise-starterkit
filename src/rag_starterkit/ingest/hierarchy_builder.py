from dataclasses import dataclass, field
from typing import List, Optional
from .toc_parser import TocItem

@dataclass
class Node:
    title: str
    level: int
    start_page: int
    end_page: Optional[int] = None
    number: Optional[str] = None
    children: List["Node"] = field(default_factory=list)

def build_tree(toc: List[TocItem]) -> Node:
    root = Node(title="ROOT", level=0, start_page=1)
    stack = [root]

    # Sort by page then level (best effort)
    # toc_sorted = sorted(toc, key=lambda x: (x.start_page, x.level))
    def _num_key(n: str):
        return [int(p) for p in n.split(".")] if n else []

    toc_sorted = sorted(
        toc,
        key=lambda x: (_num_key(x.number), x.start_page)
    )

    for item in toc_sorted:
        node = Node(title=item.title, level=item.level, start_page=item.start_page, number=item.number)

        while stack and stack[-1].level >= node.level:
            stack.pop()
        stack[-1].children.append(node)
        stack.append(node)

    # Set end_page using next sibling/ancestor boundaries
    def assign_end_pages(n: Node):
        for i, ch in enumerate(n.children):
            next_start = n.children[i + 1].start_page if i + 1 < len(n.children) else None
            ch.end_page = (next_start - 1) if next_start else n.end_page
            assign_end_pages(ch)

    # Root end_page left None (full doc); fill in later from doc length
    assign_end_pages(root)
    return root
