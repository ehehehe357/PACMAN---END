"""
Test phần đối kháng (Minimax / Alpha-Beta / hàm đánh giá / vòng lặp chơi).

Chạy (từ thư mục gốc dự án):
    python -m unittest tests.test_multiagent -v
"""

import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.helpers import load_state, signature, state_from_text           # noqa: E402
from src import evaluation as ev                                           # noqa: E402
from src.multiAgents import (                                              # noqa: E402
    AlphaBetaAgent, ChaseGhost, ExpectimaxAgent, MinimaxAgent, RandomGhost,
    create_agent, format_stats, play_game,
)

# ---------------------------------------------------------------- bản đồ nhỏ dựng tay
IMMEDIATE_WIN = """\
%%%%%%%
%     %
%P.   %
%     %
%    G%
%%%%%%%
"""

GHOST_ADJACENT = """\
%%%%%%%
%     %
%PG.  %
%     %
%%%%%%%
"""

FORCED_LOSS = """\
%%%%%%
%PG. %
%%%%%%
"""

NO_GHOST = """\
%%%%%%%
%P . .%
%%%%%%%
"""

SEPARATED = """\
%%%%%%%%%%
%P . %. .%
% . G%. .%
%%%%%%%%%%
"""


def random_states(map_name, n_states, max_walk, seed):
    """Sinh trạng thái đa dạng bằng cách đi ngẫu nhiên một vài bước từ trạng thái đầu."""
    rng = random.Random(seed)
    result = [load_state(map_name)]
    for _ in range(n_states):
        s = load_state(map_name)
        for _ in range(rng.randint(1, max_walk)):
            for idx in range(1 + len(s.get_ghost_positions())):
                acts = s.get_legal_actions(idx)
                if not acts:
                    break
                s = s.generate_successor(idx, rng.choice(acts))
        if not (s.is_win() or s.is_lose()):
            result.append(s)
    return result


class TestMinimaxBehaviour(unittest.TestCase):
    def test_01_takes_immediate_win(self):
        """Còn đúng 1 mồi ngay cạnh, Ghost ở xa -> mọi độ sâu đều ăn luôn để thắng."""
        for depth in (1, 2, 3):
            agent = MinimaxAgent(depth=depth)
            self.assertEqual(agent.get_action(state_from_text(IMMEDIATE_WIN)), "EAST")
            self.assertGreater(agent.last_stats["value"], ev.WIN_VALUE / 2)

    def test_02_avoids_stepping_into_adjacent_ghost(self):
        """Ghost sát cạnh: đi vào Ghost là thua ngay -> không được chọn EAST."""
        for cls in (MinimaxAgent, AlphaBetaAgent):
            agent = cls(depth=2)
            action = agent.get_action(state_from_text(GHOST_ADJACENT))
            self.assertIn(action, ("NORTH", "SOUTH"))
            self.assertGreater(agent.last_stats["value"], ev.LOSE_VALUE / 2)

    def test_03_forced_loss_detected(self):
        """Chỉ còn nước đâm vào Ghost -> giá trị phải là giá trị thua."""
        agent = MinimaxAgent(depth=3)
        action = agent.get_action(state_from_text(FORCED_LOSS))
        self.assertEqual(action, "EAST")
        self.assertLess(agent.last_stats["value"], ev.LOSE_VALUE / 2)

    def test_04_no_legal_action_in_terminal_state(self):
        """Trạng thái đã kết thúc -> get_action trả None, không lỗi."""
        lost = state_from_text(FORCED_LOSS).generate_successor(0, "EAST")
        self.assertTrue(lost.is_lose())
        agent = AlphaBetaAgent(depth=2)
        self.assertIsNone(agent.get_action(lost))
        self.assertEqual(agent.last_stats["nodes"], 1)

    def test_05_works_without_ghosts(self):
        """Không có Ghost: cây chỉ có nút MAX, agent vẫn chạy và đi về phía mồi."""
        state = state_from_text(NO_GHOST)
        for cls in (MinimaxAgent, AlphaBetaAgent):
            agent = cls(depth=2)
            self.assertEqual(agent.get_action(state), "EAST")
            self.assertEqual(agent._num_agents, 1)

    def test_06_does_not_mutate_input_state(self):
        state = load_state("adv_maze")
        before = signature(state)
        for agent in (MinimaxAgent(depth=2), AlphaBetaAgent(depth=2), ExpectimaxAgent(depth=2)):
            agent.get_action(state)
        self.assertEqual(signature(state), before)

    def test_07_invalid_depth_rejected(self):
        with self.assertRaises(ValueError):
            MinimaxAgent(depth=0)


class TestAlphaBetaEquivalence(unittest.TestCase):
    """Yêu cầu đề 3.5: cùng trạng thái, độ sâu, hàm đánh giá -> kết quả tương đương."""

    CASES = [
        ("adv_tiny", (1, 2, 3, 4)),
        ("adv_trap", (1, 2, 3)),
        ("adv_open", (1, 2, 3)),
        ("adv_maze", (1, 2, 3)),
        ("adv_two_ghosts", (1, 2)),
    ]

    def test_08_same_action_and_value_on_many_states(self):
        checked = 0
        for map_name, depths in self.CASES:
            for state in random_states(map_name, n_states=6, max_walk=8, seed=7):
                for depth in depths:
                    for eval_name in ("maze", "manhattan", "score", "voronoi"):
                        fn = ev.EVALUATION_FUNCTIONS[eval_name]
                        mm = MinimaxAgent(depth, fn)
                        ab = AlphaBetaAgent(depth, fn)
                        a_mm, a_ab = mm.get_action(state), ab.get_action(state)
                        ctx = f"{map_name} depth={depth} eval={eval_name}"
                        self.assertEqual(a_mm, a_ab, ctx)
                        self.assertAlmostEqual(mm.last_stats["value"], ab.last_stats["value"], msg=ctx)
                        checked += 1
        self.assertGreater(checked, 100)

    def test_09_alphabeta_never_expands_more_and_sometimes_fewer(self):
        strictly_fewer = 0
        for map_name, depths in self.CASES:
            for state in random_states(map_name, n_states=4, max_walk=6, seed=11):
                for depth in depths:
                    mm, ab = MinimaxAgent(depth), AlphaBetaAgent(depth)
                    mm.get_action(state)
                    ab.get_action(state)
                    self.assertLessEqual(ab.last_stats["nodes"], mm.last_stats["nodes"])
                    if ab.last_stats["nodes"] < mm.last_stats["nodes"]:
                        strictly_fewer += 1
        self.assertGreater(strictly_fewer, 0)

    def test_10_alphabeta_prunes_clearly_at_depth_3(self):
        state = load_state("adv_open")
        mm, ab = MinimaxAgent(3), AlphaBetaAgent(3)
        mm.get_action(state)
        ab.get_action(state)
        self.assertLess(ab.last_stats["nodes"], 0.8 * mm.last_stats["nodes"])


class TestNodeCounting(unittest.TestCase):
    def test_11_minimax_node_count_matches_manual_enumeration(self):
        """Đếm độc lập số nút của cây độ sâu 1 (1 Ghost) và so với bộ đếm của agent."""
        state = load_state("adv_open")
        expected = 1                                         # nút gốc
        for a in state.get_legal_actions(0):
            child = state.generate_successor(0, a)
            expected += 1                                    # nút Ghost
            if child.is_win() or child.is_lose():
                continue
            expected += len(child.get_legal_actions(1))      # các lá sau nước đi của Ghost
        agent = MinimaxAgent(depth=1)
        agent.get_action(state)
        self.assertEqual(agent.last_stats["nodes"], expected)

    def test_12_deeper_search_expands_more_nodes(self):
        state = load_state("adv_maze")
        counts = []
        for depth in (1, 2, 3):
            agent = MinimaxAgent(depth)
            agent.get_action(state)
            counts.append(agent.last_stats["nodes"])
        self.assertTrue(counts[0] < counts[1] < counts[2], counts)

    def test_13_stats_contain_all_required_fields(self):
        """Mục 4 của đề: tác tử, độ sâu, hành động, giá trị, số trạng thái, thời gian."""
        agent = create_agent("alphabeta", depth=2)
        agent.get_action(load_state("adv_tiny"))
        stats = agent.last_stats
        for key in ("agent", "depth", "action", "value", "nodes", "time_ms"):
            self.assertIn(key, stats)
        self.assertEqual(stats["agent"], "AlphaBeta")
        self.assertEqual(stats["depth"], 2)
        self.assertGreater(stats["nodes"], 1)
        self.assertGreaterEqual(stats["time_ms"], 0.0)
        self.assertIn("AlphaBeta", format_stats(stats))


class TestMultiGhost(unittest.TestCase):
    def test_14_two_ghosts_agent_order_and_equivalence(self):
        state = load_state("adv_two_ghosts")
        self.assertEqual(len(state.get_ghost_positions()), 2)
        mm, ab = MinimaxAgent(2), AlphaBetaAgent(2)
        self.assertEqual(mm.get_action(state), ab.get_action(state))
        self.assertEqual(mm._num_agents, 3)
        self.assertLess(ab.last_stats["nodes"], mm.last_stats["nodes"])

    def test_15_expectimax_value_is_not_below_minimax(self):
        """Trung bình >= min tại mọi nút Ghost nên giá trị gốc Expectimax >= Minimax."""
        for state in random_states("adv_maze", 5, 6, seed=3):
            mm, ex = MinimaxAgent(2), ExpectimaxAgent(2)
            mm.get_action(state)
            ex.get_action(state)
            self.assertGreaterEqual(ex.last_stats["value"] + 1e-9, mm.last_stats["value"])


class TestEvaluation(unittest.TestCase):
    def test_16_terminal_ordering_win_gt_normal_gt_lose(self):
        normal = state_from_text(IMMEDIATE_WIN)
        won = normal.generate_successor(0, "EAST")
        lost = state_from_text(FORCED_LOSS).generate_successor(0, "EAST")
        for fn in ev.EVALUATION_FUNCTIONS.values():
            self.assertGreater(fn(won), fn(normal))
            self.assertGreater(fn(normal), fn(lost))

    def test_17_closer_to_food_is_better(self):
        near = state_from_text("%%%%%%%%%\n%  P.   %\n%%%%%%%%%\n")
        far = state_from_text("%%%%%%%%%\n%P    . %\n%%%%%%%%%\n")
        self.assertGreater(ev.maze_evaluation(near), ev.maze_evaluation(far))

    def test_18_closer_ghost_is_worse(self):
        close = state_from_text("%%%%%%%%%\n%P G   .%\n%%%%%%%%%\n")
        far = state_from_text("%%%%%%%%%\n%P    G.%\n%%%%%%%%%\n")
        self.assertLess(ev.maze_evaluation(close), ev.maze_evaluation(far))

    def test_19_maze_distance_respects_walls(self):
        """Manhattan = 2 nhưng đường thật phải đi vòng -> maze_distance lớn hơn."""
        state = state_from_text("%%%%%\n%P%.%\n%   %\n%%%%%\n")
        pac = state.get_pacman_position()
        food = ev.grid_positions(state.get_food())[0]
        manhattan = abs(pac[0] - food[0]) + abs(pac[1] - food[1])
        self.assertEqual(manhattan, 2)
        self.assertEqual(ev.maze_distance(state.get_walls(), pac, food), 4)

    def test_20_unreachable_ghost_and_food_are_handled(self):
        """Bản đồ có vùng không liên thông: không lỗi, không phạt Ghost ở vùng khác."""
        state = state_from_text(SEPARATED)
        value = ev.maze_evaluation(state)
        self.assertTrue(value == value and abs(value) != float("inf"))       # không NaN / inf
        # Đưa Ghost sang cùng vùng thì giá trị phải thấp hơn (bị phạt)
        same_zone = state_from_text(SEPARATED.replace("G%. .", " %. .").replace("%P . ", "%P G "))
        self.assertLess(ev.maze_evaluation(same_zone), value)


    def test_20b_voronoi_equals_maze_without_ghosts_and_penalizes_close_ghost(self):
        no_ghost = state_from_text(NO_GHOST)
        self.assertAlmostEqual(ev.voronoi_evaluation(no_ghost), ev.maze_evaluation(no_ghost))
        close = state_from_text("%%%%%%%%%\n%P G   .%\n%%%%%%%%%\n")
        far = state_from_text("%%%%%%%%%\n%P    G.%\n%%%%%%%%%\n")
        self.assertLess(ev.voronoi_evaluation(close), ev.voronoi_evaluation(far))


class TestGameLoop(unittest.TestCase):
    def test_21_game_is_reproducible_with_seeded_ghosts(self):
        def run():
            ghosts = [ChaseGhost(0.8, seed=5)]
            return play_game(load_state("adv_tiny"), AlphaBetaAgent(2), ghosts, max_moves=60)
        r1, r2 = run(), run()
        self.assertEqual((r1["outcome"], r1["score"], r1["moves"]), (r2["outcome"], r2["score"], r2["moves"]))

    def test_22_minimax_and_alphabeta_play_identical_games(self):
        for map_name in ("adv_tiny", "adv_trap", "adv_maze"):
            res = []
            for cls in (MinimaxAgent, AlphaBetaAgent):
                ghosts = [ChaseGhost(0.8, seed=1)]
                res.append(play_game(load_state(map_name), cls(2), ghosts, max_moves=80))
            self.assertEqual(
                [d["action"] for d in res[0]["decisions"]],
                [d["action"] for d in res[1]["decisions"]], map_name)
            self.assertEqual(res[0]["score"], res[1]["score"])
            self.assertLessEqual(res[1]["total_nodes"], res[0]["total_nodes"])

    def test_23_game_reports_outcome_and_counts(self):
        res = play_game(state_from_text(IMMEDIATE_WIN), MinimaxAgent(2), [RandomGhost(0)])
        self.assertEqual(res["outcome"], "win")
        self.assertEqual(res["moves"], 1)
        self.assertEqual(len(res["decisions"]), 1)

    def test_24_timeout_on_map_with_unreachable_food(self):
        """Mồi nằm ở vùng không tới được: không thể thắng, trò chơi phải dừng bằng timeout."""
        res = play_game(state_from_text(SEPARATED), AlphaBetaAgent(2), [RandomGhost(0)], max_moves=25)
        self.assertIn(res["outcome"], ("timeout", "lose"))
        self.assertNotEqual(res["outcome"], "win")

    def test_25_on_step_callback_is_called_for_every_agent_move(self):
        calls = []
        play_game(load_state("adv_tiny"), AlphaBetaAgent(1), [RandomGhost(2)], max_moves=5,
                  on_step=lambda s, idx, act, st: calls.append((idx, st is not None)))
        self.assertIn((0, True), calls)
        self.assertTrue(all(has_stats == (idx == 0) for idx, has_stats in calls))


class TestEngineIntegration(unittest.TestCase):
    """Kiểm tra phối hợp với engine thật: vòng lặp Game và luật thắng của engine."""

    def test_28_runs_inside_engine_game_loop(self):
        """Agent + Ghost chạy được trong Game.run() của engine (get_action(state) một tham số)."""
        from src.engine import Game

        class FakeDisplay:
            def __init__(self):
                self.updates = 0

            def initialize(self, state):
                pass

            def update(self, state):
                self.updates += 1
                if self.updates > 400:                       # chống treo nếu ván không kết thúc
                    raise RuntimeError("ván chơi không kết thúc")

        display = FakeDisplay()
        game = Game([AlphaBetaAgent(2), ChaseGhost(0.8, seed=1, index=1)], display, load_state("adv_tiny"))
        game.run()
        self.assertTrue(game.state.is_win() or game.state.is_lose())
        self.assertGreater(display.updates, 0)

    def test_29_engine_requires_eating_capsule_to_win(self):
        """Engine chỉ báo thắng khi hết mồi VÀ hết capsule -> agent phải đi ăn nốt capsule."""
        state = state_from_text("%%%%%%%%\n%P.o  G%\n%%%%%%%%\n")
        after_food = state.generate_successor(0, "EAST")
        self.assertEqual(after_food.get_num_food(), 0)
        self.assertFalse(after_food.is_win())                 # còn capsule nên chưa thắng
        res = play_game(state, AlphaBetaAgent(3), [ChaseGhost(1.0, seed=0, index=1)], max_moves=10)
        self.assertEqual(res["outcome"], "win")
        self.assertEqual(res["moves"], 2)


class TestFactory(unittest.TestCase):
    def test_26_create_agent_names(self):
        self.assertIsInstance(create_agent("minimax"), MinimaxAgent)
        self.assertIsInstance(create_agent("Alpha-Beta"), AlphaBetaAgent)
        self.assertIsInstance(create_agent("expectimax", depth=3), ExpectimaxAgent)

    def test_27_create_agent_rejects_unknown_names(self):
        with self.assertRaises(ValueError):
            create_agent("bogus")
        with self.assertRaises(ValueError):
            create_agent("minimax", evaluation="bogus")


if __name__ == "__main__":
    unittest.main(verbosity=2)
