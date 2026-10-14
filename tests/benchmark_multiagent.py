"""
Thực nghiệm phần đối kháng (đề mục 5.3): Minimax vs Alpha-Beta ở nhiều độ sâu.

Chạy từ thư mục gốc dự án:
    python tests/benchmark_multiagent.py              # chạy đủ 3 thực nghiệm, ghi vào results/
    python tests/benchmark_multiagent.py --quick      # bản rút gọn (ít seed) để thử nhanh
    python tests/benchmark_multiagent.py --charts-only   # vẽ lại biểu đồ từ CSV có sẵn
    python tests/benchmark_multiagent.py --demo --map adv_maze --agent alphabeta --depth 3
                                                      # xem từng quyết định của một ván

Kết quả:
    results/multiagent_decisions.csv   TN A: quyết định tại trạng thái ban đầu (hành động, giá trị, nodes, thời gian)
    results/multiagent_games.csv       TN B: cả ván chơi (kết quả, điểm, tổng nodes, thời gian TB mỗi quyết định)
    results/multiagent_eval.csv        TN C: so sánh hàm đánh giá
    results/multiagent_charts.png      biểu đồ minh hoạ
"""

import argparse
import csv
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.helpers import ROOT, load_state                                   # noqa: E402
from src.evaluation import EVALUATION_FUNCTIONS                              # noqa: E402
from src.multiAgents import (                                                # noqa: E402
    ChaseGhost, RandomGhost, create_agent, format_stats, play_game,
)

RESULTS_DIR = os.path.join(ROOT, "results")

# (tên bản đồ, độ sâu tối đa dùng cho TN A) - đặc điểm khác nhau theo yêu cầu mục 5
MAPS = [
    ("adv_tiny", 4),          # bản đồ nhỏ
    ("adv_open", 4),          # bản đồ lớn, ÍT vật cản
    ("adv_maze", 4),          # bản đồ lớn, NHIỀU vật cản + capsule
    ("adv_trap", 4),          # có ngõ cụt / bẫy
    ("adv_two_ghosts", 4),    # nhiều Ghost
]
GAME_DEPTHS = (1, 2, 3)
MAX_MOVES = 300          # adv_open có 118 mồi, cần ~150-200 nước để thắng


def write_csv(name, rows):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"  -> {os.path.relpath(path, ROOT)} ({len(rows)} dòng)")
    return path


# -----------------------------------------------------------------------------
# TN A: một quyết định tại trạng thái ban đầu
# -----------------------------------------------------------------------------
def experiment_decisions():
    print("TN A: quyết định tại trạng thái ban đầu")
    rows = []
    for map_name, max_depth in MAPS:
        for depth in range(1, max_depth + 1):
            per_agent = {}
            for agent_name in ("minimax", "alphabeta"):
                agent = create_agent(agent_name, depth=depth)
                agent.get_action(load_state(map_name))
                s = agent.last_stats
                per_agent[agent_name] = s
                rows.append({
                    "map": map_name, "agent": s["agent"], "depth": depth,
                    "action": s["action"], "value": round(s["value"], 3),
                    "nodes": s["nodes"], "time_ms": round(s["time_ms"], 3),
                })
            mm, ab = per_agent["minimax"], per_agent["alphabeta"]
            assert mm["action"] == ab["action"] and abs(mm["value"] - ab["value"]) < 1e-9, \
                f"Minimax != AlphaBeta tại {map_name} depth={depth}"
            print(f"  {map_name:15s} d={depth}  nodes {mm['nodes']:>6} -> {ab['nodes']:>6}"
                  f"  (giảm {100 * (1 - ab['nodes'] / mm['nodes']):4.1f}%)   action={mm['action']}")
    write_csv("multiagent_decisions.csv", rows)
    return rows


# -----------------------------------------------------------------------------
# TN B: chơi cả ván
# -----------------------------------------------------------------------------
GHOST_TYPES = {
    "chase0.8": lambda n, seed: [ChaseGhost(0.8, seed=seed * 10 + i, index=i + 1) for i in range(n)],
    "random": lambda n, seed: [RandomGhost(seed=seed * 10 + i, index=i + 1) for i in range(n)],
}


def experiment_games(seeds):
    print(f"TN B: chơi cả ván ({len(seeds)} seed / cấu hình)")
    rows = []
    for map_name, _ in MAPS:
        for ghost_type, make_ghosts in GHOST_TYPES.items():
            for depth in GAME_DEPTHS:
                for agent_name in ("minimax", "alphabeta", "expectimax"):
                    if agent_name == "expectimax" and depth == 3 and map_name == "adv_open":
                        continue                    # bỏ cấu hình chậm nhất, không cần thiết cho so sánh
                    for seed in seeds:
                        state = load_state(map_name)
                        ghosts = make_ghosts(len(state.get_ghost_positions()), seed)
                        agent = create_agent(agent_name, depth=depth)
                        res = play_game(state, agent, ghosts, max_moves=MAX_MOVES)
                        rows.append({
                            "map": map_name, "ghost": ghost_type, "agent": agent.name,
                            "depth": depth, "seed": seed, "outcome": res["outcome"],
                            "score": res["score"], "moves": res["moves"],
                            "total_nodes": res["total_nodes"],
                            "avg_time_ms": round(res["avg_time_ms"], 3),
                        })
            print(f"  {map_name:15s} {ghost_type:9s} xong", flush=True)
    write_csv("multiagent_games.csv", rows)
    return rows


# -----------------------------------------------------------------------------
# TN C: hàm đánh giá
# -----------------------------------------------------------------------------
def experiment_eval(seeds):
    print("TN C: so sánh hàm đánh giá (AlphaBeta, depth 2, ChaseGhost 0.8)")
    rows = []
    for map_name, _ in MAPS:
        for eval_name in EVALUATION_FUNCTIONS:
            for seed in seeds:
                state = load_state(map_name)
                ghosts = GHOST_TYPES["chase0.8"](len(state.get_ghost_positions()), seed)
                agent = create_agent("alphabeta", depth=2, evaluation=eval_name)
                res = play_game(state, agent, ghosts, max_moves=MAX_MOVES)
                rows.append({
                    "map": map_name, "evaluation": eval_name, "seed": seed,
                    "outcome": res["outcome"], "score": res["score"], "moves": res["moves"],
                    "total_nodes": res["total_nodes"],
                })
    write_csv("multiagent_eval.csv", rows)
    return rows


# -----------------------------------------------------------------------------
# Tóm tắt + biểu đồ
# -----------------------------------------------------------------------------
def summarize_games(rows):
    print("\nTóm tắt TN B (trung bình theo bản đồ/Ghost/agent/độ sâu):")
    print(f"  {'map':15s} {'ghost':9s} {'agent':10s} d  win lose tmo  score   nodes/ván  ms/quyết định")
    groups = {}
    for r in rows:
        groups.setdefault((r["map"], r["ghost"], r["agent"], r["depth"]), []).append(r)
    for (m, g, a, d), rs in groups.items():
        wins = sum(r["outcome"] == "win" for r in rs)
        loses = sum(r["outcome"] == "lose" for r in rs)
        tmo = len(rs) - wins - loses
        print(f"  {m:15s} {g:9s} {a:10s} {d}  {wins:3d} {loses:4d} {tmo:3d} "
              f"{statistics.mean(r['score'] for r in rs):7.1f} "
              f"{statistics.mean(r['total_nodes'] for r in rs):10.0f} "
              f"{statistics.mean(r['avg_time_ms'] for r in rs):10.2f}")


def load_rows(name):
    """Đọc lại CSV (ép kiểu số) để vẽ biểu đồ mà không cần chạy lại thực nghiệm."""
    with open(os.path.join(RESULTS_DIR, name), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for key in ("depth", "nodes", "total_nodes", "moves", "seed"):
            if key in r:
                r[key] = int(r[key])
    return rows


def make_charts(decision_rows, game_rows):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  (bỏ qua biểu đồ: chưa cài matplotlib)")
        return

    fig, axes = plt.subplots(1, 3, figsize=(17, 4.8))

    # (1) nodes theo độ sâu
    ax = axes[0]
    for i, (map_name, _) in enumerate(MAPS):
        for agent, style in (("Minimax", "--"), ("AlphaBeta", "-")):
            pts = [(r["depth"], r["nodes"]) for r in decision_rows
                   if r["map"] == map_name and r["agent"] == agent]
            ax.plot(*zip(*pts), style, marker="o", color=f"C{i}", label=f"{map_name} / {agent}")
    ax.set_yscale("log")
    ax.set_xlabel("Độ sâu"); ax.set_ylabel("Số trạng thái đã xét (log)")
    ax.set_title("A. Nodes tại trạng thái đầu\n(nét đứt: Minimax, nét liền: Alpha-Beta)")
    ax.set_xticks(range(1, 5)); ax.grid(alpha=.3); ax.legend(fontsize=6, ncol=2)

    # (2) % giảm nodes
    ax = axes[1]
    for map_name, _ in MAPS:
        mm = {r["depth"]: r["nodes"] for r in decision_rows if r["map"] == map_name and r["agent"] == "Minimax"}
        ab = {r["depth"]: r["nodes"] for r in decision_rows if r["map"] == map_name and r["agent"] == "AlphaBeta"}
        depths = sorted(mm)
        ax.plot(depths, [100 * (1 - ab[d] / mm[d]) for d in depths], marker="o", label=map_name)
    ax.set_xlabel("Độ sâu"); ax.set_ylabel("% trạng thái được cắt tỉa")
    ax.set_title("B. Mức tiết kiệm của Alpha-Beta so với Minimax")
    ax.set_xticks(range(1, 5)); ax.grid(alpha=.3); ax.legend(fontsize=7)

    # (3) tỉ lệ thắng theo độ sâu (Alpha-Beta, Ghost đuổi)
    ax = axes[2]
    for map_name, _ in MAPS:
        xs, ys = [], []
        for d in GAME_DEPTHS:
            rs = [r for r in game_rows if r["map"] == map_name and r["agent"] == "AlphaBeta"
                  and r["ghost"] == "chase0.8" and r["depth"] == d]
            if rs:
                xs.append(d); ys.append(100 * sum(r["outcome"] == "win" for r in rs) / len(rs))
        ax.plot(xs, ys, marker="o", label=map_name)
    ax.set_xlabel("Độ sâu"); ax.set_ylabel("Tỉ lệ thắng (%)")
    ax.set_title("C. Tỉ lệ thắng của Alpha-Beta (Ghost đuổi 0.8)")
    ax.set_xticks(GAME_DEPTHS); ax.set_ylim(-5, 105); ax.grid(alpha=.3); ax.legend(fontsize=7)

    fig.tight_layout()
    path = os.path.join(RESULTS_DIR, "multiagent_charts.png")
    fig.savefig(path, dpi=140)
    print(f"  -> {os.path.relpath(path, ROOT)}")


# -----------------------------------------------------------------------------
def demo(args):
    state = load_state(args.map)
    agent = create_agent(args.agent, depth=args.depth, evaluation=args.eval)
    ghosts = GHOST_TYPES[args.ghost](len(state.get_ghost_positions()), args.seed)

    def show(s, idx, action, stats):
        if stats:
            print(f"[Pacman] {format_stats(stats)}")
        else:
            print(f"         Ghost {idx} -> {action}")

    res = play_game(state, agent, ghosts, max_moves=args.max_moves, on_step=show)
    print(f"\nKết quả: {res['outcome'].upper()} | điểm={res['score']} | số nước={res['moves']} | "
          f"tổng nodes={res['total_nodes']} | TB {res['avg_time_ms']:.2f} ms/quyết định")


def main():
    p = argparse.ArgumentParser(description="Thực nghiệm Minimax / Alpha-Beta cho Pacman")
    p.add_argument("--quick", action="store_true", help="ít seed hơn, chạy nhanh")
    p.add_argument("--demo", action="store_true", help="chạy một ván và in từng quyết định")
    p.add_argument("--charts-only", action="store_true", help="vẽ lại biểu đồ từ CSV đã có")
    p.add_argument("--map", default="adv_maze")
    p.add_argument("--agent", default="alphabeta", choices=["minimax", "alphabeta", "expectimax"])
    p.add_argument("--depth", type=int, default=2)
    p.add_argument("--eval", default="maze", choices=sorted(EVALUATION_FUNCTIONS))
    p.add_argument("--ghost", default="chase0.8", choices=sorted(GHOST_TYPES))
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--max-moves", type=int, default=MAX_MOVES)
    args = p.parse_args()

    if args.demo:
        return demo(args)
    if args.charts_only:
        return make_charts(load_rows("multiagent_decisions.csv"), load_rows("multiagent_games.csv"))

    seeds = range(2) if args.quick else range(5)
    dec = experiment_decisions()
    games = experiment_games(seeds)
    experiment_eval(seeds)
    summarize_games(games)
    make_charts(dec, games)


if __name__ == "__main__":
    main()
