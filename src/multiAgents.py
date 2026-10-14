"""
multiAgents.py - Tìm kiếm đối kháng cho Pacman (đề mục 3.5 và 5.3).

Nội dung:
    MinimaxAgent     : Minimax giới hạn độ sâu.
    AlphaBetaAgent   : Alpha-Beta Pruning (cùng kết quả với Minimax, ít trạng thái hơn).
    ExpectimaxAgent  : (mở rộng, tuỳ chọn) Ghost được mô hình hoá là ngẫu nhiên.
    RandomGhost / ChaseGhost : các chính sách điều khiển Ghost khi chạy mô phỏng.
                       Dùng được trực tiếp trong Game.run() của engine:
                       Game([pacman_agent, ChaseGhost(index=1), ChaseGhost(index=2)], display, state)
    play_game        : vòng lặp chơi cả ván, thu thập số liệu cho báo cáo / giao diện.
    create_agent     : hàm tạo agent theo tên (dành cho menu giao diện).

Quy ước (phải nêu rõ trong báo cáo):
    * Agent 0 = Pacman (MAX); agent 1..n = các Ghost (MIN), lần lượt đi sau Pacman.
    * 1 "ply" = một agent đi một nước. 1 mức độ sâu (depth) = 1 vòng đủ:
      Pacman đi + tất cả Ghost đi. depth = 2 với 1 Ghost nghĩa là nhìn trước 4 ply.
    * "Số trạng thái đã xét" (nodes) = số lần thăm một nút của cây tìm kiếm
      (gồm nút gốc, nút trung gian và nút lá). Minimax và Alpha-Beta đếm theo
      cùng định nghĩa nên so sánh trực tiếp được.
    * Khi nhiều nước đi cùng giá trị, chọn nước ĐẦU TIÊN theo thứ tự của
      state.get_legal_actions() -> kết quả xác định (deterministic), nhờ đó
      Minimax và Alpha-Beta luôn chọn cùng một hành động.

API cần từ GameState (khớp skeleton src/engine.py):
    get_legal_actions(agent_index), generate_successor(agent_index, action),
    get_ghost_positions(), get_walls(), get_pacman_position(),
    is_win(), is_lose(), get_score()  (+ những gì hàm đánh giá dùng).
"""

import random
import time

try:                                    # chạy từ thư mục gốc:  python main.py / python -m unittest
    from src.evaluation import EVALUATION_FUNCTIONS, bfs_distances, maze_evaluation
except ImportError:                     # chạy trực tiếp trong thư mục src/
    from evaluation import EVALUATION_FUNCTIONS, bfs_distances, maze_evaluation

INF = float("inf")


# =============================================================================
# 1. AGENT CỦA PACMAN
# =============================================================================
class AdversarialAgent:
    """
    Lớp cha: quản lý độ sâu, hàm đánh giá, bộ đếm trạng thái, đo thời gian và
    ghi lại thông tin quyết định (mục 4 của đề: 'Với chế độ đối kháng').

    Lớp con chỉ cần cài đặt `_choose(state, legal_actions)`.
    """

    name = "Adversarial"

    def __init__(self, depth=2, evaluation_fn=None):
        if depth < 1:
            raise ValueError("depth phải >= 1")
        self.depth = depth
        self.evaluation_fn = evaluation_fn or maze_evaluation
        self.nodes = 0                  # số trạng thái đã xét trong lần ra quyết định hiện tại
        self.last_stats = None          # thông tin lần quyết định gần nhất (dict)
        self._num_agents = 1

    # ---------------------------------------------------------------- public
    def get_action(self, state):
        """Trả về hành động tốt nhất cho Pacman (None nếu không còn nước đi)."""
        legal = state.get_legal_actions(0)
        self._num_agents = 1 + len(state.get_ghost_positions())
        self.nodes = 0

        if not legal:                   # trạng thái kết thúc
            self.nodes = 1
            self.last_stats = self._make_stats(None, self.evaluation_fn(state), {}, 0.0)
            return None

        start = time.perf_counter()
        action, value, action_values = self._choose(state, legal)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        self.last_stats = self._make_stats(action, value, action_values, elapsed_ms)
        return action

    # ------------------------------------------------------------- để lớp con
    def _choose(self, state, legal):
        raise NotImplementedError

    # --------------------------------------------------------------- tiện ích
    def _make_stats(self, action, value, action_values, elapsed_ms):
        return {
            "agent": self.name,                 # tác tử đã sử dụng
            "depth": self.depth,                # độ sâu tìm kiếm
            "evaluation": getattr(self.evaluation_fn, "__name__", "custom"),
            "action": action,                   # hành động được chọn
            "value": value,                     # giá trị đánh giá của hành động được chọn
            "nodes": self.nodes,                # số trạng thái đã xét
            "time_ms": elapsed_ms,              # thời gian ra quyết định
            "action_values": action_values,     # giá trị từng hành động ở gốc (xem ghi chú ở AlphaBeta)
        }

    def _next(self, agent, depth):
        """(agent kế tiếp, depth kế tiếp). Depth tăng khi quay lại Pacman."""
        nxt = agent + 1
        if nxt == self._num_agents:
            return 0, depth + 1
        return nxt, depth

    def _is_leaf(self, state, depth):
        return state.is_win() or state.is_lose() or depth >= self.depth


# -----------------------------------------------------------------------------
class MinimaxAgent(AdversarialAgent):
    """
    Minimax: Pacman cực đại hoá, mọi Ghost cực tiểu hoá giá trị đánh giá
    (giả định Ghost chơi tối ưu để làm Pacman tệ nhất).
    """

    name = "Minimax"

    def _choose(self, state, legal):
        self.nodes = 1                                  # nút gốc
        next_agent, next_depth = self._next(0, 0)

        best_action, best_value = None, -INF
        action_values = {}
        for action in legal:
            child = state.generate_successor(0, action)
            value = self._value(child, next_agent, next_depth)
            action_values[action] = value
            if value > best_value:                      # '>' => giữ nước đầu tiên khi hoà
                best_action, best_value = action, value
        return best_action, best_value, action_values

    def _value(self, state, agent, depth):
        self.nodes += 1
        if self._is_leaf(state, depth):
            return self.evaluation_fn(state)
        actions = state.get_legal_actions(agent)
        if not actions:
            return self.evaluation_fn(state)

        next_agent, next_depth = self._next(agent, depth)
        values = [
            self._value(state.generate_successor(agent, a), next_agent, next_depth)
            for a in actions
        ]
        return max(values) if agent == 0 else min(values)


# -----------------------------------------------------------------------------
class AlphaBetaAgent(AdversarialAgent):
    """
    Alpha-Beta Pruning. Cắt tỉa CHỈ khi vượt NGHIÊM NGẶT (v > beta ở MAX, v < alpha ở MIN):
      -> giá trị trả về của nút gốc luôn bằng Minimax,
      -> kết hợp tie-break 'nước đầu tiên', hành động được chọn luôn trùng Minimax.

    Ghi chú: `action_values` của Alpha-Beta chỉ chính xác cho hành động được chọn;
    các hành động còn lại có thể là cận trên (do bị cắt tỉa), không phải giá trị thật.
    """

    name = "AlphaBeta"

    def _choose(self, state, legal):
        self.nodes = 1
        next_agent, next_depth = self._next(0, 0)

        alpha, beta = -INF, INF
        best_action, best_value = None, -INF
        action_values = {}
        for action in legal:
            child = state.generate_successor(0, action)
            value = self._value(child, next_agent, next_depth, alpha, beta)
            action_values[action] = value
            if value > best_value:
                best_action, best_value = action, value
            alpha = max(alpha, best_value)
        return best_action, best_value, action_values

    def _value(self, state, agent, depth, alpha, beta):
        self.nodes += 1
        if self._is_leaf(state, depth):
            return self.evaluation_fn(state)
        actions = state.get_legal_actions(agent)
        if not actions:
            return self.evaluation_fn(state)

        next_agent, next_depth = self._next(agent, depth)

        if agent == 0:                                  # MAX
            v = -INF
            for a in actions:
                child = state.generate_successor(agent, a)
                v = max(v, self._value(child, next_agent, next_depth, alpha, beta))
                if v > beta:                            # cắt tỉa beta
                    return v
                alpha = max(alpha, v)
            return v

        v = INF                                         # MIN
        for a in actions:
            child = state.generate_successor(agent, a)
            v = min(v, self._value(child, next_agent, next_depth, alpha, beta))
            if v < alpha:                               # cắt tỉa alpha
                return v
            beta = min(beta, v)
        return v


# -----------------------------------------------------------------------------
class ExpectimaxAgent(MinimaxAgent):
    """
    (Mở rộng, không bắt buộc) Ghost được coi là đi ngẫu nhiên đều -> nút Ghost lấy
    TRUNG BÌNH thay vì MIN. Hợp với RandomGhost; kém an toàn hơn Minimax với ChaseGhost.
    """

    name = "Expectimax"

    def _value(self, state, agent, depth):
        self.nodes += 1
        if self._is_leaf(state, depth):
            return self.evaluation_fn(state)
        actions = state.get_legal_actions(agent)
        if not actions:
            return self.evaluation_fn(state)

        next_agent, next_depth = self._next(agent, depth)
        values = [
            self._value(state.generate_successor(agent, a), next_agent, next_depth)
            for a in actions
        ]
        return max(values) if agent == 0 else sum(values) / len(values)


# =============================================================================
# 2. CHÍNH SÁCH CỦA GHOST (dùng khi mô phỏng ván chơi)
# =============================================================================
class RandomGhost:
    """Ghost đi ngẫu nhiên (có seed để tái lập kết quả)."""

    name = "RandomGhost"

    def __init__(self, seed=None, index=1):
        self.index = index              # chỉ số agent của Ghost này (1, 2, ...)
        self.rng = random.Random(seed)

    def get_action(self, state, agent_index=None):
        # Game.run() của engine gọi get_action(state) -> dùng self.index.
        # play_game() truyền agent_index tường minh.
        agent_index = self.index if agent_index is None else agent_index
        actions = state.get_legal_actions(agent_index)
        return self.rng.choice(actions) if actions else None


class ChaseGhost:
    """
    Ghost đuổi Pacman: với xác suất `chase_prob` đi nước làm giảm khoảng cách đường đi
    thật tới Pacman, ngược lại đi ngẫu nhiên. chase_prob = 1.0 là Ghost 'xấu nhất' cho Pacman.
    """

    name = "ChaseGhost"

    def __init__(self, chase_prob=0.8, seed=None, index=1):
        self.index = index
        self.chase_prob = chase_prob
        self.rng = random.Random(seed)

    def get_action(self, state, agent_index=None):
        agent_index = self.index if agent_index is None else agent_index
        actions = state.get_legal_actions(agent_index)
        if not actions:
            return None
        if self.rng.random() > self.chase_prob:
            return self.rng.choice(actions)

        dist = bfs_distances(state.get_walls(), state.get_pacman_position())
        best, best_d = [], INF
        for a in actions:
            ghost_pos = state.generate_successor(agent_index, a).get_ghost_positions()[agent_index - 1]
            d = dist.get(ghost_pos, INF)
            if d < best_d:
                best, best_d = [a], d
            elif d == best_d:
                best.append(a)
        return self.rng.choice(best)


# =============================================================================
# 3. VÒNG LẶP CHƠI + THU THẬP SỐ LIỆU
# =============================================================================
def play_game(state, pacman_agent, ghost_agents=None, max_moves=200, on_step=None):
    """
    Chơi một ván từ `state` cho đến khi thắng / thua / hết `max_moves` nước của Pacman.

    on_step(state, agent_index, action, stats): callback sau MỖI nước đi (kể cả Ghost),
    để giao diện vẽ lại; `stats` là pacman_agent.last_stats khi agent_index == 0, ngược lại None.

    Trả về dict: outcome ('win' | 'lose' | 'timeout'), score, moves, final_state,
    decisions (list stats từng quyết định của Pacman), total_nodes, avg_time_ms.
    """
    num_ghosts = len(state.get_ghost_positions())
    if ghost_agents is None:
        ghost_agents = [RandomGhost(index=i + 1, seed=i) for i in range(num_ghosts)]

    decisions = []
    moves = 0
    while not (state.is_win() or state.is_lose()) and moves < max_moves:
        action = pacman_agent.get_action(state)
        if action is None:
            break
        stats = dict(pacman_agent.last_stats)
        decisions.append(stats)
        state = state.generate_successor(0, action)
        moves += 1
        if on_step:
            on_step(state, 0, action, stats)

        for index, ghost in enumerate(ghost_agents, start=1):
            if state.is_win() or state.is_lose():
                break
            g_action = ghost.get_action(state, index)
            if g_action is None:
                continue
            state = state.generate_successor(index, g_action)
            if on_step:
                on_step(state, index, g_action, None)

    if state.is_win():
        outcome = "win"
    elif state.is_lose():
        outcome = "lose"
    else:
        outcome = "timeout"

    total_nodes = sum(d["nodes"] for d in decisions)
    total_time = sum(d["time_ms"] for d in decisions)
    return {
        "outcome": outcome,
        "score": state.get_score(),
        "moves": moves,
        "final_state": state,
        "decisions": decisions,
        "total_nodes": total_nodes,
        "avg_time_ms": total_time / len(decisions) if decisions else 0.0,
    }


# =============================================================================
# 4. TIỆN ÍCH CHO GIAO DIỆN / MENU
# =============================================================================
AGENTS = {
    "minimax": MinimaxAgent,
    "alphabeta": AlphaBetaAgent,
    "expectimax": ExpectimaxAgent,
}


def create_agent(name, depth=2, evaluation="maze"):
    """create_agent('alphabeta', depth=3, evaluation='maze') -> AlphaBetaAgent."""
    key = name.lower().replace("-", "").replace("_", "")
    if key not in AGENTS:
        raise ValueError(f"Agent không hợp lệ: {name!r}. Chọn một trong {sorted(AGENTS)}")
    if callable(evaluation):
        eval_fn = evaluation
    elif evaluation in EVALUATION_FUNCTIONS:
        eval_fn = EVALUATION_FUNCTIONS[evaluation]
    else:
        raise ValueError(f"Hàm đánh giá không hợp lệ: {evaluation!r}. Chọn một trong {sorted(EVALUATION_FUNCTIONS)}")
    return AGENTS[key](depth=depth, evaluation_fn=eval_fn)


def format_stats(stats):
    """Chuỗi một dòng để hiển thị trên giao diện hoặc in console (mục 4 của đề)."""
    return (
        f"{stats['agent']} | depth={stats['depth']} | action={stats['action']} | "
        f"value={stats['value']:.2f} | nodes={stats['nodes']} | time={stats['time_ms']:.2f} ms"
    )
