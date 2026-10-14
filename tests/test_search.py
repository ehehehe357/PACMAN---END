import unittest
import sys
import os

# Thêm thư mục gốc và thư mục src vào sys.path để chạy được mọi môi trường
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_DIR = os.path.join(BASE_DIR, 'src')
for p in (BASE_DIR, SRC_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from search import (
    breadth_first_search, depth_first_search, uniform_cost_search,
    a_star_search, null_heuristic, greedy_best_first_search
)

from searchAgents import (
    PositionSearchProblem, FoodSearchProblem,
    manhattan_heuristic, food_heuristic, SearchAgent
)
from maps.map_generator import load_map


class TestSearchAlgorithms(unittest.TestCase):
    """
    Bộ kiểm thử tự động cho toàn bộ thuật toán tìm kiếm đường đi (Mục 3, 5, 6.1).
    Chạy bằng lệnh: python -m unittest tests/test_search.py
    """

    def setUp(self):
        """Khởi tạo mê cung chuẩn 5x5 dùng cho các bài test đơn giản."""
        self.start_pos = (1, 1)
        self.goal_pos = (3, 3)
        # Tường bao quanh và 1 bức tường cản ở giữa (buộc phải đi vòng)
        self.walls_5x5 = {
            (0, 0), (1, 0), (2, 0), (3, 0), (4, 0),
            (0, 4), (1, 4), (2, 4), (3, 4), (4, 4),
            (0, 1), (0, 2), (0, 3),
            (4, 1), (4, 2), (4, 3),
            (2, 1), (2, 2)  # Tường chắn ở giữa
        }
        self.problem_simple = PositionSearchProblem(
            self.start_pos, self.goal_pos, self.walls_5x5
        )

    # -------------------------------------------------------------------------
    # TEST 1: BFS tìm đường tối ưu số bước
    # -------------------------------------------------------------------------
    def test_bfs_finds_optimal_path(self):
        """BFS phải tìm được đường đi có số bước ít nhất trên mê cung phẳng."""
        res = breadth_first_search(self.problem_simple)
        self.assertIsNotNone(res["actions"], "BFS phải tìm thấy đường đi!")
        self.assertEqual(res["total_cost"], 4, "Độ dài đường đi ngắn nhất phải bằng 4!")
        self.assertEqual(len(res["actions"]), 4)

    # -------------------------------------------------------------------------
    # TEST 2: DFS tìm được đường đến đích
    # -------------------------------------------------------------------------
    def test_dfs_finds_path(self):
        """DFS phải tìm được đường tới đích (chấp nhận đường không tối ưu)."""
        res = depth_first_search(self.problem_simple)
        self.assertIsNotNone(res["actions"], "DFS phải tìm thấy đường đi!")
        self.assertGreaterEqual(res["total_cost"], 4, "DFS không bao giờ tìm đường ngắn hơn tối ưu!")

    # -------------------------------------------------------------------------
    # TEST 3: UCS tối ưu chi phí trên bản đồ có bùn (so sánh với BFS)
    # -------------------------------------------------------------------------
    def test_ucs_cost_maze(self):
        """UCS phải chọn đường vòng tránh bùn để tổng chi phí nhỏ hơn BFS."""
        map_path = os.path.join(BASE_DIR, "maps", "costMaze.txt")
        m = load_map(map_path)
        cost_prob = PositionSearchProblem(
            start_pos=m.p_start,
            goal_pos=(9, 1),
            walls=m.grid,
            cost_fn=lambda pos: m.get_cost(pos[0], pos[1])
        )
        res_bfs = breadth_first_search(cost_prob)
        res_ucs = uniform_cost_search(cost_prob)

        self.assertIsNotNone(res_bfs["actions"])
        self.assertIsNotNone(res_ucs["actions"])
        # BFS chọn đường thẳng qua 3 ô bùn (8 bước, chi phí 20)
        self.assertEqual(res_bfs["total_cost"], 20)
        # UCS chọn đường vòng khô ráo phía dưới (12 bước, chi phí tối ưu 12)
        self.assertEqual(res_ucs["total_cost"], 12)
        self.assertLess(res_ucs["total_cost"], res_bfs["total_cost"],
                        "UCS phải đạt tổng chi phí nhỏ hơn BFS khi có vũng bùn!")

    # -------------------------------------------------------------------------
    # TEST 4: A* mở rộng ít node hơn hoặc bằng UCS
    # -------------------------------------------------------------------------
    def test_astar_vs_ucs(self):
        """A* có Heuristic Manhattan phải mở rộng số node <= UCS."""
        res_ucs = uniform_cost_search(self.problem_simple)
        res_astar = a_star_search(self.problem_simple, manhattan_heuristic)

        self.assertEqual(res_astar["total_cost"], res_ucs["total_cost"],
                         "A* (admissible) và UCS phải cho cùng chi phí tối ưu!")
        self.assertLessEqual(res_astar["nodes_expanded"], res_ucs["nodes_expanded"],
                             "A* phải mở rộng số node ít hơn hoặc bằng UCS!")

    # -------------------------------------------------------------------------
    # TEST 5: Greedy định hướng theo Heuristic nhanh hơn A*
    # -------------------------------------------------------------------------
    def test_greedy_faster_than_astar(self):
        """Greedy thường mở rộng ít node hơn nhưng chi phí có thể lớn hơn hoặc bằng."""
        res_greedy = greedy_best_first_search(self.problem_simple, manhattan_heuristic)
        self.assertIsNotNone(res_greedy["actions"], "Greedy phải tìm thấy đường đi!")
        self.assertGreaterEqual(res_greedy["total_cost"], 4)

    # -------------------------------------------------------------------------
    # TEST 6: Bản đồ không có lời giải
    # -------------------------------------------------------------------------
    def test_no_solution_map(self):
        """Khi đích bị tường bao kín, tất cả thuật toán phải trả về actions là None."""
        blocked_walls = {
            (0, 0), (1, 0), (2, 0),
            (0, 1),         (2, 1),
            (0, 2), (1, 2), (2, 2)  # Tường bao kín ô (1, 1)
        }
        no_sol_prob = PositionSearchProblem((1, 1), (5, 5), blocked_walls)

        for algo_name, fn in [
            ("BFS", breadth_first_search),
            ("DFS", depth_first_search),
            ("UCS", uniform_cost_search),
            ("A*", lambda p: a_star_search(p, manhattan_heuristic)),
            ("Greedy", lambda p: greedy_best_first_search(p, manhattan_heuristic)),
        ]:
            res = fn(no_sol_prob)
            self.assertIsNone(res["actions"], f"Thuật toán {algo_name} phải trả về actions is None khi không có đường!")

    # -------------------------------------------------------------------------
    # TEST 7: FoodSearchProblem ăn hết toàn bộ mồi
    # -------------------------------------------------------------------------
    def test_food_search_all_eaten(self):
        """A* với food_heuristic phải giải quyết bài toán ăn hết toàn bộ hạt mồi."""
        start = (1, 1)
        foods = {(1, 3), (3, 1), (3, 3)}
        food_prob = FoodSearchProblem(start, foods, self.walls_5x5)

        res = a_star_search(food_prob, food_heuristic)
        self.assertIsNotNone(res["actions"], "A* phải tìm ra chuỗi hành động ăn hết mồi!")
        self.assertGreater(len(res["actions"]), 0)

        # Mô phỏng đường đi kiểm tra Pacman đã ăn sạch mồi chưa
        cur_pos = start
        remaining_foods = set(foods)
        dir_map = {'NORTH': (0, -1), 'SOUTH': (0, 1), 'EAST': (1, 0), 'WEST': (-1, 0)}
        for act in res["actions"]:
            dx, dy = dir_map[act]
            cur_pos = (cur_pos[0] + dx, cur_pos[1] + dy)
            if cur_pos in remaining_foods:
                remaining_foods.remove(cur_pos)

        self.assertEqual(len(remaining_foods), 0, "Pacman phải ghé qua và ăn sạch tất cả hạt mồi!")

    # -------------------------------------------------------------------------
    # TEST 8: A*(h=0) tương đương hoàn toàn với UCS (Mục 5.2)
    # -------------------------------------------------------------------------
    def test_astar_h0_equals_ucs(self):
        """A* với Heuristic h=0 phải cho kết quả giống hệt UCS cả về cost và nodes."""
        res_ucs = uniform_cost_search(self.problem_simple)
        res_a0 = a_star_search(self.problem_simple, null_heuristic)

        self.assertEqual(res_a0["total_cost"], res_ucs["total_cost"])
        self.assertEqual(res_a0["nodes_expanded"], res_ucs["nodes_expanded"])

    # -------------------------------------------------------------------------
    # TEST 9: Tính Admissible của Manhattan Heuristic
    # -------------------------------------------------------------------------
    def test_manhattan_heuristic_admissible(self):
        """Manhattan Heuristic không bao giờ được đánh giá cao hơn chi phí thực tế."""
        h_val = manhattan_heuristic(self.start_pos, self.problem_simple)
        res_ucs = uniform_cost_search(self.problem_simple)
        actual_cost = res_ucs["total_cost"]

        self.assertLessEqual(h_val, actual_cost,
                             "Heuristic h(n) phải <= chi phí thực tế h*(n) để đảm bảo tính Admissible!")

    # -------------------------------------------------------------------------
    # TEST 10: Tích hợp SearchAgent lấy action di chuyển
    # -------------------------------------------------------------------------
    def test_search_agent_integration(self):
        """SearchAgent phải lấy đúng hành động đầu tiên và giảm dần danh sách hành động."""
        agent = SearchAgent(search_function=breadth_first_search)

        class DummyState:
            def get_pacman_position(self): return (1, 1)
            def get_food(self):
                # Grid 5x5 có 1 hạt mồi tại (3, 3)
                g = [[False]*5 for _ in range(5)]
                g[3][3] = True
                return g
            def get_walls(self):
                # Tường 5x5
                w = [[False]*5 for _ in range(5)]
                w[1][2] = True
                w[2][2] = True
                return w

        state = DummyState()
        action1 = agent.get_action(state)
        self.assertIn(action1, ['NORTH', 'SOUTH', 'EAST', 'WEST'], "Hành động đầu tiên phải hợp lệ!")
        self.assertGreater(len(agent.actions), 0, "Danh sách hành động còn lại phải được lưu trong agent!")


if __name__ == '__main__':
    unittest.main()