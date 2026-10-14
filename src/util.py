import heapq
from collections import deque

class Stack:
    """Cấu trúc ngăn xếp LIFO phục vụ cho DFS"""
    def __init__(self):
        self.list = []

    def push(self, item):
        self.list.append(item)

    def pop(self):
        return self.list.pop()

    def is_empty(self):
        return len(self.list) == 0


class Queue:
    """Cấu trúc hàng đợi FIFO phục vụ cho BFS"""
    def __init__(self):
        self.list = deque()

    def push(self, item):
        self.list.append(item)

    def pop(self):
        return self.list.popleft()

    def is_empty(self):
        return len(self.list) == 0


class PriorityQueue:
    """Hàng đợi ưu tiên phục vụ cho UCS, Greedy và A*"""
    def __init__(self):
        self.heap = []
        self.count = 0  # Tránh lỗi so sánh khi hai phần tử có cùng độ ưu tiên

    def push(self, item, priority):
        entry = (priority, self.count, item)
        heapq.heappush(self.heap, entry)
        self.count += 1

    def pop(self):
        _, _, item = heapq.heappop(self.heap)
        return item

    def is_empty(self):
        return len(self.heap) == 0