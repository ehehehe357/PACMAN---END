"""
helpers.py - Tiện ích dùng chung cho test/benchmark phần đối kháng, chạy trên ENGINE THẬT của nhóm
(src/engine.py: GameState, src/map_loader.py: load_map).

Định dạng bản đồ (map_loader):  % tường | . mồi | o capsule | P Pacman | G Ghost | ' ' ô trống
Quy ước toạ độ của engine: (x, y), x = cột, y = hàng đếm TỪ TRÊN XUỐNG; walls[y][x], food_grid[y][x].
NORTH = (0, -1), SOUTH = (0, +1), WEST = (-1, 0), EAST = (+1, 0).
"""

import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.engine import GameState          # noqa: E402
from src.map_loader import load_map       # noqa: E402

MAPS_DIR = os.path.join(ROOT, "maps")


def load_state(map_name_or_path):
    """Nạp bản đồ -> GameState. 'adv_tiny' / 'adv_tiny.txt' (trong maps/) hoặc đường dẫn đầy đủ."""
    path = map_name_or_path
    if not os.path.isfile(path):
        name = map_name_or_path if map_name_or_path.endswith(".txt") else map_name_or_path + ".txt"
        path = os.path.join(MAPS_DIR, name)
    return GameState(load_map(path))


def state_from_text(text):
    """Dựng GameState từ chuỗi bản đồ (dùng cho test). map_loader chỉ đọc file nên ghi ra file tạm."""
    fd, path = tempfile.mkstemp(suffix=".txt", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        return GameState(load_map(path))
    finally:
        os.remove(path)


def signature(state):
    """Ảnh chụp đầy đủ của state (kể cả lưới mồi) để kiểm tra state không bị sửa ngoài ý muốn."""
    return (
        tuple(state.get_pacman_position()),
        tuple(tuple(g) for g in state.get_ghost_positions()),
        state.get_score(),
        tuple(tuple(row) for row in state.get_food()),
        tuple(state.get_capsules()),
        state.is_win(),
        state.is_lose(),
    )
