"""
evaluation.py - Hàm đánh giá trạng thái cho tìm kiếm đối kháng (Minimax / Alpha-Beta).

Mọi hàm đánh giá có cùng chữ ký:  f(state) -> float
Giá trị càng CAO càng có lợi cho Pacman (MAX), càng THẤP càng có lợi cho Ghost (MIN).

Các hàm cung cấp (để so sánh trong thực nghiệm 5.3):
    score_evaluation     : chỉ dùng điểm của engine (baseline đơn giản nhất).
    manhattan_evaluation : điểm + khoảng cách Manhattan tới mồi / Ghost (rẻ, bỏ qua tường).
    maze_evaluation      : điểm + khoảng cách ĐƯỜNG ĐI THẬT (BFS có tường)  <-- mặc định.
    voronoi_evaluation   : maze_evaluation + "vùng an toàn" (số ô tới được trước Ghost).

Giả định về GameState (khớp skeleton src/engine.py):
    get_pacman_position() -> (x, y)
    get_ghost_positions() -> [(x, y), ...]
    get_food()            -> grid 2D, truy cập grid[y][x] (True nếu còn mồi)
    get_walls()           -> grid 2D, truy cập grid[y][x] (True nếu là tường)
    get_capsules()        -> [(x, y), ...]
    get_score(), is_win(), is_lose()

Engine của nhóm index theo grid[y][x] (hàng trước, cột sau; y tăng khi đi xuống) nên
GRID_INDEX_XY = False. Toạ độ vị trí vẫn là tuple (x, y).
"""

from collections import deque

INF = float("inf")

# ----------------------------------------------------------------------------
# Cấu hình
# ----------------------------------------------------------------------------
GRID_INDEX_XY = False       # engine của nhóm dùng grid[y][x] (hàng trước, cột sau)

WIN_VALUE = 100000.0        # cộng thêm khi thắng  (thắng nhanh -> điểm engine cao hơn -> tốt hơn)
LOSE_VALUE = -100000.0      # cộng thêm khi thua   (thua muộn  -> điểm engine cao hơn -> đỡ tệ hơn)

W_FOOD = 10.0               # thưởng 1/khoảng cách tới mồi gần nhất
W_CAPSULE = 4.0             # thưởng 1/khoảng cách tới capsule gần nhất
W_GHOST = 30.0              # phạt cho mỗi đơn vị Ghost lọt vào bán kính nguy hiểm
GHOST_DANGER_RADIUS = 4     # Ghost cách Pacman < bán kính này mới bị phạt
W_TERRITORY = 1.5           # thưởng cho mỗi ô mà Pacman tới được TRƯỚC mọi Ghost (voronoi_evaluation)


# ----------------------------------------------------------------------------
# Tiện ích truy cập grid (tách riêng để dễ đổi cấu trúc dữ liệu của engine)
# ----------------------------------------------------------------------------
def _cell(grid, x, y):
    return grid[x][y] if GRID_INDEX_XY else grid[y][x]


def _grid_size(grid):
    """Trả về (width, height) theo đúng quy ước index."""
    if GRID_INDEX_XY:
        return len(grid), len(grid[0])
    return len(grid[0]), len(grid)


def grid_positions(grid):
    """Danh sách toạ độ (x, y) của các ô True trong grid (dùng cho food)."""
    if hasattr(grid, "asList"):                 # tương thích Grid kiểu Berkeley
        return list(grid.asList())
    width, height = _grid_size(grid)
    return [(x, y) for x in range(width) for y in range(height) if _cell(grid, x, y)]


# ----------------------------------------------------------------------------
# Khoảng cách đường đi thật (BFS) - có cache theo bản đồ
# ----------------------------------------------------------------------------
class _MapInfo:
    """Danh sách kề của bản đồ + cache bản đồ khoảng cách BFS theo từng vị trí xuất phát."""

    def __init__(self, walls):
        self.walls = walls
        width, height = _grid_size(walls)
        self.neighbors = {}
        for x in range(width):
            for y in range(height):
                if _cell(walls, x, y):
                    continue
                around = []
                for dx, dy in ((0, 1), (0, -1), (-1, 0), (1, 0)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height and not _cell(walls, nx, ny):
                        around.append((nx, ny))
                self.neighbors[(x, y)] = around
        self._dist_cache = {}

    def distances_from(self, start):
        """dict {ô: số bước ngắn nhất từ start}. Ô không tới được sẽ không có trong dict."""
        cached = self._dist_cache.get(start)
        if cached is not None:
            return cached
        dist = {start: 0}
        queue = deque([start])
        while queue:
            cur = queue.popleft()
            d = dist[cur] + 1
            for nxt in self.neighbors.get(cur, ()):
                if nxt not in dist:
                    dist[nxt] = d
                    queue.append(nxt)
        self._dist_cache[start] = dist
        return dist


_MAP_CACHE = {"info": None}


def get_map_info(walls):
    """
    Trả về _MapInfo của bản đồ. Tường không đổi trong suốt ván chơi nên chỉ dựng 1 lần.
    Kiểm tra bằng `is` (nhanh), nếu engine deepcopy tường mỗi lần thì so sánh `==`.
    LƯU Ý cho engine: nên CHIA SẺ `walls` giữa các state thay vì deepcopy để cache hiệu quả.
    """
    info = _MAP_CACHE["info"]
    if info is not None and (info.walls is walls or info.walls == walls):
        return info
    info = _MapInfo(walls)
    _MAP_CACHE["info"] = info
    return info


def maze_distance(walls, a, b):
    """Khoảng cách đường đi ngắn nhất a -> b (INF nếu không có đường)."""
    return get_map_info(walls).distances_from(a).get(b, INF)


def bfs_distances(walls, start):
    """Bản đồ khoảng cách BFS từ start (dùng cho Ghost đuổi theo Pacman)."""
    return get_map_info(walls).distances_from(start)


# ----------------------------------------------------------------------------
# Xử lý trạng thái kết thúc (dùng chung cho mọi hàm đánh giá)
# ----------------------------------------------------------------------------
def _terminal_value(state):
    """Giá trị của trạng thái kết thúc, hoặc None nếu chưa kết thúc."""
    if state.is_lose():
        return LOSE_VALUE + state.get_score()
    if state.is_win():
        return WIN_VALUE + state.get_score()
    return None


# ----------------------------------------------------------------------------
# Các hàm đánh giá
# ----------------------------------------------------------------------------
def score_evaluation(state):
    """Baseline: chỉ dùng điểm số hiện tại của engine."""
    terminal = _terminal_value(state)
    if terminal is not None:
        return terminal
    return float(state.get_score())


def manhattan_evaluation(state):
    """Điểm + khoảng cách Manhattan (bỏ qua tường). Rẻ nhưng dễ bị đánh lừa bởi tường."""
    terminal = _terminal_value(state)
    if terminal is not None:
        return terminal

    px, py = state.get_pacman_position()
    value = float(state.get_score())

    foods = grid_positions(state.get_food())
    if foods:
        d = min(abs(px - fx) + abs(py - fy) for fx, fy in foods)
        value += W_FOOD / max(d, 1)

    for gx, gy in state.get_ghost_positions():
        d = abs(px - gx) + abs(py - gy)
        if d < GHOST_DANGER_RADIUS:
            value -= W_GHOST * (GHOST_DANGER_RADIUS - d)
    return value


def maze_evaluation(state):
    """
    Hàm đánh giá mặc định - dùng khoảng cách đường đi thật (BFS có tường):

        V(s) = score(s)
               + W_FOOD    / d(Pacman, mồi gần nhất)
               + W_CAPSULE / d(Pacman, capsule gần nhất)
               - W_GHOST * Σ_g max(0, R - d(Pacman, g))        (R = GHOST_DANGER_RADIUS)

    Ý nghĩa từng thành phần:
      * score(s)  : engine đã thưởng +10 mồi, +50 capsule, -1 mỗi bước, ±500 thắng/thua
                    -> không cần cộng thêm "số mồi còn lại" (sẽ bị tính hai lần).
      * 1/d_food  : kéo Pacman về phía mồi gần nhất; dùng đường đi thật để không bị
                    "tường chắn" đánh lừa như Manhattan.
      * phạt Ghost: tăng dần khi Ghost đến gần; Ghost ở khác vùng liên thông (d = INF)
                    thì không bị phạt.
      * Trạng thái thắng/thua trả về ±100000 + score nên luôn lớn/nhỏ hơn mọi trạng thái thường.
    """
    terminal = _terminal_value(state)
    if terminal is not None:
        return terminal

    walls = state.get_walls()
    pos = state.get_pacman_position()
    dist = get_map_info(walls).distances_from(pos)

    value = float(state.get_score())

    # --- mồi gần nhất ---
    d_food = INF
    for f in grid_positions(state.get_food()):
        d = dist.get(f, INF)
        if d < d_food:
            d_food = d
    if d_food < INF:
        value += W_FOOD / max(d_food, 1)

    # --- capsule gần nhất ---
    d_cap = INF
    for c in state.get_capsules():
        d = dist.get(c, INF)
        if d < d_cap:
            d_cap = d
    if d_cap < INF:
        value += W_CAPSULE / max(d_cap, 1)

    # --- Ghost ---
    for g in state.get_ghost_positions():
        d = dist.get(g, INF)
        if d < GHOST_DANGER_RADIUS:
            value -= W_GHOST * (GHOST_DANGER_RADIUS - d)

    return value


def voronoi_evaluation(state):
    """
    maze_evaluation + thành phần "vùng an toàn" (Voronoi territory):

        V(s) = maze_evaluation(s) + W_TERRITORY * |{ô c : d(Pacman, c) < min_g d(Ghost_g, c)}|

    Ý tưởng: một ô thuộc "lãnh thổ" Pacman nếu Pacman tới đó sớm hơn mọi Ghost. Lãnh thổ nhỏ
    nghĩa là Pacman đang bị dồn vào góc / ngõ cụt - điều mà khoảng cách tới Ghost đơn thuần
    không phát hiện được cho đến khi quá muộn (hiệu ứng chân trời của tìm kiếm có giới hạn
    độ sâu). Không có Ghost thì thành phần này là hằng số nên không ảnh hưởng quyết định.
    """
    terminal = _terminal_value(state)
    if terminal is not None:
        return terminal

    value = maze_evaluation(state)
    ghosts = state.get_ghost_positions()
    if not ghosts:
        return value

    info = get_map_info(state.get_walls())
    d_pac = info.distances_from(state.get_pacman_position())
    d_ghosts = [info.distances_from(g) for g in ghosts]

    territory = 0
    for cell, dp in d_pac.items():
        for dg in d_ghosts:
            if dg.get(cell, INF) <= dp:
                break
        else:
            territory += 1
    return value + W_TERRITORY * territory


EVALUATION_FUNCTIONS = {
    "score": score_evaluation,
    "manhattan": manhattan_evaluation,
    "maze": maze_evaluation,
    "voronoi": voronoi_evaluation,
}
