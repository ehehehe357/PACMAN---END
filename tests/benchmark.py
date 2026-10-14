"""
=============================================================================
THỰC NGHIỆM TÌM KIẾM ĐƯỜNG ĐI (ĐỀ MỤC 5, 5.1, 5.2)
=============================================================================
So sánh 5 thuật toán: DFS, BFS, UCS, Greedy Best-First, A* Search.

Đặc điểm bộ thực nghiệm:
  1. Chi phí đồng đều (Tiny, Medium, Big): Tự sinh trực tiếp trong RAM (seed=42)
     bởi module gen_map, đảm bảo 100% tính tái lập số liệu.
  2. Chi phí không đồng đều: Đủ bộ 3 size Nhỏ (costMaze), Vừa (costMaze_medium),
     Lớn (costMaze_big) với địa hình bùn lầy (cost=5).
  3. Bản đồ không có lời giải (adv_nosolution): Kiểm tra an toàn không lặp vô tận.
  4. Bài toán nhiều mục tiêu (foodMaze): Pacman ăn sạch tất cả hạt mồi (FoodSearchProblem).

Cách chạy từ thư mục gốc dự án:
    python tests/benchmark.py                 # Chạy toàn bộ và vẽ biểu đồ
    python tests/benchmark.py --charts-only   # Vẽ lại biểu đồ từ CSV đã có

Kết quả sinh ra:
    results/benchmark_results.csv     # Bảng số liệu chi tiết (đưa vào Mục 5.1 & 5)
    results/performance_charts.png    # 3 biểu đồ trực quan (đưa vào Mục 5.1 & 5.2)
=============================================================================
"""

import argparse
import csv
import os
import sys
import time

# Thiết lập đường dẫn gốc dự án để import src và maps thuận tiện
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.search import (
    breadth_first_search,
    depth_first_search,
    uniform_cost_search,
    a_star_search,
    null_heuristic,
    greedy_best_first_search,
)
from src.searchAgents import (
    PositionSearchProblem,
    FoodSearchProblem,
    manhattan_heuristic,
    food_heuristic,
)
from maps.map_generator import load_map, MapData
from maps.gen_map import gen_map

RESULTS_DIR = os.path.join(ROOT, "results")
MAPS_DIR = os.path.join(ROOT, "maps")
BENCHMARK_SEED = 42


# =============================================================================
# PHẦN 1: CẤU HÌNH DANH SÁCH BẢN ĐỒ THỰC NGHIỆM (MỤC 5)
# =============================================================================
BENCHMARK_CASES = [
    # --- Nhóm 1: Bản đồ chi phí đồng nhất (Tự sinh trong RAM qua gen_map) ---
    {
        "name": "tinyMaze",
        "type": "single_goal",
        "source": "generated",
        "map_type": 1,
        "desc": "Map nhỏ (tự sinh 21x11), ít vật cản",
    },
    {
        "name": "mediumMaze",
        "type": "single_goal",
        "source": "generated",
        "map_type": 2,
        "desc": "Map vừa (tự sinh 27x15), phân nhánh",
    },
    {
        "name": "bigMaze",
        "type": "single_goal",
        "source": "generated",
        "map_type": 3,
        "desc": "Map lớn (tự sinh 33x19), bùng nổ không gian trạng thái",
    },

    # --- Nhóm 2: Bản đồ chi phí không đồng nhất (Bùn lầy ~ cost=5) ---
    {
        "name": "costMaze (Small)",
        "type": "single_goal",
        "source": "file",
        "file": "costMaze.txt",
        "goal_pos": (9, 1),
        "desc": "Map nhỏ có bùn (11x5: BFS 20 cost vs UCS 12 cost)",
    },
    {
        "name": "costMaze_medium",
        "type": "single_goal",
        "source": "file",
        "file": "costMaze_medium.txt",
        "goal_pos": (19, 1),
        "desc": "Map vừa có bùn (21x11: BFS 58 cost vs UCS 40 cost)",
    },
    {
        "name": "costMaze_big",
        "type": "single_goal",
        "source": "file",
        "file": "costMaze_big.txt",
        "goal_pos": (31, 1),
        "desc": "Map lớn có bùn (33x17: BFS 66 cost vs UCS 38 cost)",
    },

    # --- Nhóm 3: Bản đồ không có lời giải (Tường chắn kín) ---
    {
        "name": "adv_nosolution",
        "type": "single_goal",
        "source": "file",
        "file": "adv_nosolution.txt",
        "goal_pos": (7, 1),
        "desc": "Tường chắn kín hoàn toàn (chứng minh thuật toán trả về None)",
    },

    # --- Nhóm 4: Bài toán nhiều mục tiêu (Ăn sạch toàn bộ mồi) ---
    {
        "name": "foodMaze (Multi-Goal)",
        "type": "multi_goal",
        "source": "file",
        "file": "foodMaze.txt",
        "desc": "Nhiều mục tiêu: Ăn hết toàn bộ hạt mồi (FoodSearchProblem)",
    },
]


def load_problem_for_case(cfg):
    """
    Nạp dữ liệu bản đồ và khởi tạo bài toán tìm kiếm tương ứng:
      - single_goal: PositionSearchProblem (tìm đường đến 1 điểm đích)
      - multi_goal : FoodSearchProblem (tìm đường ăn sạch mồi)
    """
    if cfg["source"] == "generated":
        # Sinh map ngẫu nhiên có kiểm soát bằng seed=42 trực tiếp trên RAM
        lines = gen_map(map_type=cfg["map_type"], with_ghost=False, seed=BENCHMARK_SEED)
        m = MapData(lines)
        goal_pos = (1, 1)
    else:
        # Đọc map từ file tĩnh
        filepath = os.path.join(MAPS_DIR, cfg["file"])
        m = load_map(filepath)
        goal_pos = cfg.get("goal_pos", (1, 1))

    # Nếu là bài toán nhiều mục tiêu (FoodSearch)
    if cfg["type"] == "multi_goal":
        foods = set()
        for r in range(m.rows):
            for c in range(m.cols):
                if m.cell(c, r) in ('.', 'o'):
                    foods.add((c, r))
        problem = FoodSearchProblem(m.p_start, foods, m.grid)
        heuristic_fn = food_heuristic
        return problem, heuristic_fn

    # Nếu là bài toán 1 đích đơn (PositionSearch)
    cost_fn = lambda pos: m.get_cost(pos[0], pos[1])
    problem = PositionSearchProblem(
        start_pos=m.p_start,
        goal_pos=goal_pos,
        walls=m.grid,
        cost_fn=cost_fn,
    )
    heuristic_fn = manhattan_heuristic
    return problem, heuristic_fn


# =============================================================================
# PHẦN 2: THỰC THI BENCHMARK & XUẤT CSV (MỤC 5.1)
# =============================================================================
def write_csv(name, rows):
    """Lưu danh sách kết quả đo đạc ra file CSV."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n[OK] Đã lưu bảng số liệu: {os.path.relpath(path, ROOT)} ({len(rows)} dòng)")
    return path


def run_benchmark():
    """Chạy lần lượt 5 thuật toán qua tất cả các bản đồ và ghi nhận số liệu."""
    print("=" * 84)
    print(f" BẮT ĐẦU BENCHMARK TÌM ĐƯỜNG (MỤC 5, 5.1, 5.2) | SEED={BENCHMARK_SEED}")
    print("=" * 84)

    rows = []
    print(f"{'Bản đồ':23s} {'Thuật toán':10s} {'Success':8s} {'Steps':7s} {'Cost':7s} {'Nodes':8s} {'Time (ms)':10s}")
    print("-" * 84)

    for cfg in BENCHMARK_CASES:
        problem, default_heuristic = load_problem_for_case(cfg)
        map_name = cfg["name"]

        # Danh sách 5 thuật toán chuẩn + biến thể A*(h=0) để đối đầu với UCS (Mục 5.2)
        algorithms = [
            ("DFS", lambda p: depth_first_search(p)),
            ("BFS", lambda p: breadth_first_search(p)),
            ("UCS", lambda p: uniform_cost_search(p)),
            ("Greedy", lambda p: greedy_best_first_search(p, default_heuristic)),
            ("A*", lambda p: a_star_search(p, default_heuristic)),
            ("A*(h=0)", lambda p: a_star_search(p, null_heuristic)),
        ]

        for algo_name, fn in algorithms:
            # Đo thời gian chính xác bằng perf_counter
            t0 = time.perf_counter()
            res = fn(problem)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            success = res["actions"] is not None
            steps = len(res["actions"]) if success else 0
            cost = res["total_cost"] if success else 0
            nodes = res["nodes_expanded"]

            rows.append({
                "Map": map_name,
                "Algorithm": algo_name,
                "Success": str(success),
                "Steps": steps,
                "Cost": cost,
                "Nodes_Expanded": nodes,
                "Time_ms": round(elapsed_ms, 3),
            })

            succ_str = "YES" if success else "NO"
            print(f"{map_name:23s} {algo_name:10s} {succ_str:8s} {steps:<7d} {cost:<7d} {nodes:<8d} {elapsed_ms:<10.2f}")
        print("-" * 84)

    write_csv("benchmark_results.csv", rows)
    return rows


# =============================================================================
# PHẦN 3: VẼ 3 BIỂU ĐỒ TRỰC QUAN (MỤC 5.1 & 5.2)
# =============================================================================
def make_charts(rows):
    """
    Vẽ 3 biểu đồ trực quan lưu vào results/performance_charts.png:
      - Biểu đồ 1: Số node mở rộng trên bigMaze (chứng minh bùng nổ trạng thái).
      - Biểu đồ 2: So sánh Chi phí vs Số bước trên costMaze (BFS dính bùn vs UCS/A*).
      - Biểu đồ 3: So sánh Heuristic (UCS vs A*) minh họa mức tiết kiệm node (Mục 5.2).
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("[!] Không tìm thấy thư viện matplotlib, bỏ qua bước vẽ biểu đồ.")
        return

    std_algos = ["DFS", "BFS", "UCS", "Greedy", "A*"]
    colors = {
        "DFS": "#e74c3c", "BFS": "#3498db", "UCS": "#f39c12",
        "Greedy": "#9b59b6", "A*": "#2ecc71"
    }

    fig, axes = plt.subplots(1, 3, figsize=(18, 5.2))

    # --- Biểu đồ 1: Số trạng thái mở rộng trên bigMaze ---
    ax1 = axes[0]
    big_rows = [r for r in rows if r["Map"] == "bigMaze" and r["Algorithm"] in std_algos]
    if big_rows:
        algos = [r["Algorithm"] for r in big_rows]
        nodes = [int(r["Nodes_Expanded"]) for r in big_rows]
        bars = ax1.bar(algos, nodes, color=[colors[a] for a in algos], width=0.55)
        ax1.set_title("1. Số nodes mở rộng trên bigMaze (Tự sinh)\n(Minh họa bùng nổ không gian trạng thái)", fontsize=11, fontweight="bold")
        ax1.set_ylabel("Số nodes mở rộng (Nodes Expanded)", fontsize=10)
        ax1.grid(axis="y", linestyle="--", alpha=0.5)
        for b in bars:
            y = b.get_height()
            ax1.text(b.get_x() + b.get_width() / 2.0, y + max(nodes) * 0.015, f"{y}", ha="center", va="bottom", fontsize=9, fontweight="bold")
        ax1.set_ylim(0, max(nodes) * 1.15)

    # --- Biểu đồ 2: Chi phí vs Số bước trên costMaze ---
    ax2 = axes[1]
    cost_rows = [r for r in rows if r["Map"] == "costMaze (Small)" and r["Algorithm"] in std_algos]
    if cost_rows:
        algos = [r["Algorithm"] for r in cost_rows]
        x_idx = np.arange(len(algos))
        w = 0.35
        costs = [int(r["Cost"]) for r in cost_rows]
        steps = [int(r["Steps"]) for r in cost_rows]

        r1 = ax2.bar(x_idx - w / 2, costs, w, label="Tổng chi phí (Cost)", color="#e67e22")
        r2 = ax2.bar(x_idx + w / 2, steps, w, label="Số bước đi (Steps)", color="#3498db")
        ax2.set_title("2. Chi phí & Số bước trên costMaze\n(UCS và A* tìm đường rẻ hơn BFS khi có vũng bùn)", fontsize=11, fontweight="bold")
        ax2.set_xticks(x_idx)
        ax2.set_xticklabels(algos)
        ax2.set_ylabel("Giá trị", fontsize=10)
        ax2.legend(fontsize=9)
        ax2.grid(axis="y", linestyle="--", alpha=0.5)
        for rect in r1:
            ax2.text(rect.get_x() + rect.get_width() / 2.0, rect.get_height() + 0.3, f"{rect.get_height()}", ha="center", va="bottom", fontsize=8)
        for rect in r2:
            ax2.text(rect.get_x() + rect.get_width() / 2.0, rect.get_height() + 0.3, f"{rect.get_height()}", ha="center", va="bottom", fontsize=8)

    # --- Biểu đồ 3: Đánh giá Heuristic mục 5.2 (UCS / A*(h=0) vs A*(Manhattan)) ---
    ax3 = axes[2]
    maps_solved = ["tinyMaze", "mediumMaze", "bigMaze", "costMaze (Small)"]
    ucs_nodes, astar_nodes, reduction_pct = [], [], []

    for m_name in maps_solved:
        u_val = next(int(r["Nodes_Expanded"]) for r in rows if r["Map"] == m_name and r["Algorithm"] == "UCS")
        a_val = next(int(r["Nodes_Expanded"]) for r in rows if r["Map"] == m_name and r["Algorithm"] == "A*")
        ucs_nodes.append(u_val)
        astar_nodes.append(a_val)
        pct = (1.0 - (a_val / u_val)) * 100.0 if u_val > 0 else 0.0
        reduction_pct.append(pct)

    x_idx = np.arange(len(maps_solved))
    w = 0.35
    b1 = ax3.bar(x_idx - w / 2, ucs_nodes, w, label="UCS / A*(h=0)", color="#95a5a6")
    b2 = ax3.bar(x_idx + w / 2, astar_nodes, w, label="A* (Heuristic)", color="#2ecc71")

    ax3.set_title("3. Đánh giá Heuristic \nSố Nodes giữa UCS và A* (Manhattan)", fontsize=11, fontweight="bold")
    ax3.set_xticks(x_idx)
    ax3.set_xticklabels(["tinyMaze", "mediumMaze", "bigMaze", "costMaze"])
    ax3.set_ylabel("Số nodes mở rộng (log scale)", fontsize=10)
    ax3.set_yscale("log")
    ax3.legend(fontsize=9)
    ax3.grid(axis="y", linestyle="--", alpha=0.5)

    # Ghi phần trăm giảm node trên thanh của A*
    for i, rect in enumerate(b2):
        pct = reduction_pct[i]
        ax3.text(rect.get_x() + rect.get_width() / 2.0, rect.get_height() * 1.15, f"-{pct:.1f}%", ha="center", va="bottom", fontsize=8, color="#27ae60", fontweight="bold")

    fig.tight_layout()
    chart_path = os.path.join(RESULTS_DIR, "performance_charts.png")
    fig.savefig(chart_path, dpi=160)
    print(f"[OK] Đã lưu biểu đồ: {os.path.relpath(chart_path, ROOT)}")


# =============================================================================
# PHẦN 4: HÀM MAIN ĐIỀU KHIỂN CLI
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="Benchmark tìm kiếm đường đi Pacman (Mục 5, 5.1, 5.2)")
    parser.add_argument("--charts-only", action="store_true", help="Chỉ vẽ lại biểu đồ từ file CSV đã có")
    args = parser.parse_args()

    # Nếu chỉ muốn vẽ lại biểu đồ
    if args.charts_only:
        csv_path = os.path.join(RESULTS_DIR, "benchmark_results.csv")
        if os.path.exists(csv_path):
            with open(csv_path, "r", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            make_charts(rows)
            return

    # Chạy toàn bộ thực nghiệm và tạo biểu đồ
    rows = run_benchmark()
    make_charts(rows)
    print("\n[HOÀN TẤT] Dữ liệu Mục 5, 5.1 và 5.2 đã được tổng hợp thành công vào thư mục results/!")


if __name__ == "__main__":
    main()