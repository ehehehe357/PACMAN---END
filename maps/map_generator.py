import os
from collections import deque

MAPS_DIR = os.path.dirname(os.path.abspath(__file__))
USE_GENERATOR = True      # True: tự sinh map mỗi lần chơi; False: đọc file tinyMaze*.txt
MAP_SEED = None           # None: mỗi lần một map khác; đặt số (vd 11) để map luôn giống nhau
MAP_SIZES = {1: (25, 17), 2: (29, 19), 3: (33, 23), 4: (10, 4)}    # (số cột, số hàng) của Tiny/Medium/Big/Unreachable

SCORE_G1 = 50
SCORE_G2 = 10

def map_path(filename):
    return os.path.join(MAPS_DIR, filename)

class MapData:
    def __init__(self, lines):
        self.lines = list(lines)
        self.grid = [list(line) for line in lines]
        self.rows = len(self.grid)
        self.cols = len(self.grid[0])
        self.p_start = None
        self.g_start = []

        for r in range (self.rows):
            for c in range (self.cols):
                ch = self.grid[r][c]
                if ch == 'P':
                    self.p_start = (c, r)
                    self.grid[r][c] = ' '
                elif ch=='G':
                    self.g_start.append ((c, r))
                    self.grid[r][c] = ' '
    def cell(self, x, y):
        if 0 <= y < self.rows and 0 <= x < self.cols:
            return self.grid[y][x]
        return '%'
    def get_cost(self, x, y):
        """Trả về chi phí bước vào ô (x, y)."""
        ch = self.cell(x, y)
        if ch == '~':
            return 5   # Vũng bùn / nước: chi phí 5
        return 1       # Đường bình thường: chi phí 
    def is_wall (self, x, y):
        return self.cell(x, y) == '%'

    def eat (self, x, y):
        ch = self.cell(x, y)
        if ch=='o':
            self.grid[y][x] = ' '
            return SCORE_G1
        if ch == '.':
            self.grid[y][x] = ' '
            return SCORE_G2
        return 0

    def goal_left(self):
        return sum(row.count('o') + row.count('.') for row in self.grid)

    def find_path(self, start, goal):
        queue = deque([start])
        came_from = {start: None}
        while queue:
            cur = queue.popleft()
            if cur == goal:
                break
            x, y = cur
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                nxt = (x + dx, y + dy)
                if nxt not in came_from and not self.is_wall(*nxt):
                    came_from[nxt] = cur
                    queue.append(nxt)

        if goal not in came_from:
            return []

        path = []
        cur = goal
        while cur != start:
            path.append(cur)
            cur = came_from[cur]
        path.reverse()
        return path

def load_map (path):
    with open(path, encoding="utf-8") as f:
        lines = [line.rstrip("\r\n") for line in f if line.strip()]
    if not lines:
        raise ValueError(f"File map rỗng: {path}")
    width = len(lines[0])
    for i, line in enumerate(lines, 1):
        if len(line) != width:
            raise ValueError(f"{path}: dòng {i} dài {len(line)} ký tự, dòng 1 dài {width}")
    return MapData(lines)

def get_map(mode, map_id):
    from maps.gen_map import gen_map
    """Mỗi lần gọi trả về 1 map: mode 1 = Người vs Ma, mode 2 = AI vs Ma (cả hai đều có ma); mode 3 = tìm đường (không ma); map_id 1/2/3 = Tiny/Medium/Big, 4 = Map cụt."""
    if map_id == 4:
        return load_map(map_path("adv_nosolution.txt"))

    if not USE_GENERATOR:
        name = "tinyMaze.txt" if mode == 3 else "tinyMaze_ghost.txt"
        return load_map(map_path(name))

    cols, rows = MAP_SIZES[map_id]
    lines = gen_map(map_id, with_ghost=(mode != 3), seed=MAP_SEED)
    return MapData(lines)


