import heapq
from typing import Any

class PrioritizedItem:
    def __init__(self, priority: int, item: Any):
        self.priority = priority
        self.item = item

    def __lt__(self, other):
        # Min-heap behavior by default; use -priority for max-heap
        return self.priority < other.priority

    def __repr__(self):
        return f"PrioritizedItem(priority={-self.priority}, item={self.item})"  # display actual priority


class DecisionHeap:
    def __init__(self):
        self._heap = []

    def push(self, item: Any, priority: int):
        heapq.heappush(self._heap, PrioritizedItem(-priority, item))  # max-heap via negation

    def pop(self) -> Any:
        if self._heap:
            return heapq.heappop(self._heap).item
        return None

    def peek(self) -> Any:
        if self._heap:
            return self._heap[0].item
        return None

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def __len__(self):
        return len(self._heap)

    def all_items(self) -> list:
        return [entry.item for entry in self._heap]
