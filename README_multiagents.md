## Phần đối kháng (Multi-agent: Minimax / Alpha-Beta)

### Tệp liên quan
| Tệp | Nội dung |
|---|---|
| `src/multiAgents.py` | `MinimaxAgent`, `AlphaBetaAgent`, `ExpectimaxAgent` (mở rộng), Ghost mô phỏng (`RandomGhost`, `ChaseGhost`), `play_game`, `create_agent` |
| `src/evaluation.py` | Hàm đánh giá: `score`, `manhattan`, `maze` (mặc định), `voronoi` |
| `tests/test_multiagent.py` | 28 test |
| `tests/benchmark_multiagent.py` | Thực nghiệm mục 5.3, ghi CSV + biểu đồ vào `results/` |
| `tests/helpers.py` | `MiniGameState` + `load_state()` dùng cho test (xem mục "Ghép với engine thật") |
| `maps/adv_*.txt` | 6 bản đồ thử nghiệm cho chế độ đối kháng |

### Lệnh chạy
```bash
# Chạy test của phần đối kháng
python -m unittest tests.test_multiagent -v

# Xem từng quyết định của một ván (thuật toán, độ sâu, hành động, giá trị, số trạng thái, thời gian)
python tests/benchmark_multiagent.py --demo --map adv_maze --agent alphabeta --depth 3

# Tái tạo toàn bộ kết quả thực nghiệm (results/multiagent_*.csv, multiagent_charts.png)
python tests/benchmark_multiagent.py            # đầy đủ (vài phút)
python tests/benchmark_multiagent.py --quick    # rút gọn
```

### Dùng trong code / giao diện
```python
from src.multiAgents import create_agent, play_game, ChaseGhost, format_stats

agent = create_agent("alphabeta", depth=3, evaluation="maze")   # "minimax" | "alphabeta" | "expectimax"
action = agent.get_action(state)          # hành động của Pacman
print(format_stats(agent.last_stats))     # tác tử, độ sâu, hành động, giá trị, nodes, thời gian

# Chạy cả ván; on_step(state, agent_index, action, stats) được gọi sau MỖI nước đi để vẽ lại UI
result = play_game(state, agent, [ChaseGhost(0.8, seed=0)], on_step=lambda s, i, a, st: ...)
```
`agent.last_stats` là dict: `agent, depth, evaluation, action, value, nodes, time_ms, action_values`.

### Quy ước thiết kế
* Agent 0 = Pacman (MAX), agent 1..n = Ghost (MIN). **1 depth = 1 vòng đủ** (Pacman + mọi Ghost).
* **Số trạng thái đã xét** = số nút được thăm trong cây tìm kiếm (gốc + trung gian + lá); Minimax và
  Alpha-Beta đếm cùng định nghĩa.
* Hoà giá trị -> chọn hành động **đầu tiên** trong `get_legal_actions()` => kết quả xác định, nên Minimax và
  Alpha-Beta luôn chọn cùng hành động (đã kiểm chứng trong `test_08`, `test_22`).
* Alpha-Beta chỉ cắt tỉa khi vượt **nghiêm ngặt** (`v > beta`, `v < alpha`).

### Ghép với engine thật (`src/engine.py`)
`multiAgents.py` và `evaluation.py` chỉ dùng API đã khai báo trong skeleton của `GameState`:
`get_legal_actions(i)`, `generate_successor(i, action)`, `get_pacman_position()`, `get_ghost_positions()`,
`get_food()`, `get_walls()`, `get_capsules()`, `get_score()`, `is_win()`, `is_lose()`.

Yêu cầu / lưu ý với engine:
1. `get_food()` và `get_walls()` truy cập được bằng `grid[x][y]`. Nếu engine dùng `grid[y][x]`, đặt
   `GRID_INDEX_XY = False` trong `src/evaluation.py`.
2. `generate_successor` **chỉ di chuyển đúng một agent** và **không sửa state gốc**.
3. Nên **chia sẻ `walls` giữa các state** (không deepcopy tường) để cache BFS của hàm đánh giá hiệu quả;
   chỉ copy food / capsules / vị trí.
4. Va chạm phải được kiểm tra sau mỗi nước đi của **cả Pacman lẫn Ghost** (`_update_win_lose_status`).
5. Sau khi engine xong, sửa thân hàm `load_state()` trong `tests/helpers.py` để trả về `GameState` thật
   (đã có TODO trong file); test và benchmark giữ nguyên.
