try:
    from src.search import SearchProblem
    from src.evaluation import grid_positions
except ImportError:
    from search import SearchProblem
    from evaluation import grid_positions

class PositionSearchProblem(SearchProblem):
    """
    Bài toán tìm đường: Pacman từ vị trí xuất phát tìm đường đến 1 điểm đích cố định.
    Trạng thái (state) ở đây đơn giản là một tuple tọa độ: (x, y)
    """

    def __init__(self, start_pos, goal_pos, walls, cost_fn=lambda x: 1):
        """
        - start_pos: Tọa độ bắt đầu của Pacman, ví dụ (1, 1)
        - goal_pos: Tọa độ đích (thức ăn), ví dụ (5, 5)
        - walls: Tập hợp set chứa các tọa độ tường, ví dụ set([(0,0), (0,1), ...])
        - cost_fn: Hàm tính chi phí bước đi (mặc định mỗi bước tốn chi phí là 1)
        """
        self.start_state = start_pos
        self.goal_state = goal_pos
        self.cost_fn = cost_fn
        # TỰ ĐỘNG CHUẨN HÓA: Hỗ trợ cả 2D grid lẫn set, tương thích cả True/False lẫn ký tự '%'
        if isinstance(walls, list):
            self.walls = {
                (x, y)
                for y, row in enumerate(walls)
                for x, is_wall in enumerate(row)
                if (is_wall is True or is_wall == '%')
            }
        else:
            self.walls = walls  # Nếu đã là set sẵn thì giữ nguyên

    def get_start_state(self):
        """Trả về trạng thái bắt đầu (x, y)"""
        return self.start_state

    def is_goal_state(self, state):
        """Kiểm tra xem tọa độ hiện tại đã trùng với tọa độ đích chưa"""
        return state == self.goal_state

    def get_successors(self, state):
        """
        Từ tọa độ hiện tại (x, y), thử đi sang 4 hướng:
        North (lên), South (xuống), East (phải), West (trái).
        Ô nào không phải là tường thì coi là kế tiếp hợp lệ.
        """
        successors = []
        x, y = state

        # Thống nhất 4 hành động và sự thay đổi tọa độ tương ứng (dx, dy)
        # Giả sử: x tăng sang phải, y tăng đi xuống dưới (theo chỉ số dòng/cột)
        actions = [
            ('NORTH', (x, y - 1)),
            ('SOUTH', (x, y + 1)),
            ('EAST',  (x + 1, y)),
            ('WEST',  (x - 1, y))
        ]

        for action, next_pos in actions:
            # Nếu vị trí kế tiếp không nằm trong tập các ô tường
            if next_pos not in self.walls:
                cost = self.cost_fn(next_pos)
                successors.append((next_pos, action, cost))

        return successors

    def get_cost_of_actions(self, actions):
            """Tính tổng chi phí thực tế dựa theo hàm cost_fn."""
            x, y = self.start_state
            total_cost = 0
            dir_map = {
                'NORTH': (0, -1), 'SOUTH': (0, 1),
                'EAST': (1, 0),   'WEST': (-1, 0)
            }
            for action in actions:
                if action in dir_map:
                    dx, dy = dir_map[action]
                    x, y = x + dx, y + dy
                    total_cost += self.cost_fn((x, y))
            return total_cost
def manhattan_heuristic(state, problem=None):
    """
    Hàm Heuristic tính khoảng cách Manhattan từ vị trí hiện tại đến đích.
    Thỏa mãn cả tính Admissible (không đánh giá quá cao) và Consistent (nhất quán).
    """
    if problem is not None and hasattr(problem, 'goal_state'):
        goal = problem.goal_state
        # state ở dạng tọa độ (x, y)
        return abs(state[0] - goal[0]) + abs(state[1] - goal[1])
    return 0

class FoodSearchProblem(SearchProblem):
    """
    Bài toán tìm đường để Pacman ăn hết toàn bộ thức ăn trên bản đồ.
    Trạng thái: (pacman_pos, remaining_foods)
      - pacman_pos: (x, y)
      - remaining_foods: frozenset chứa các tọa độ (x, y) của thức ăn chưa ăn
    """

    def __init__(self, start_pos, foods_set, walls):
        """
        - start_pos: tọa độ bắt đầu của Pacman (x, y)
        - foods_set: tập hợp (set/frozenset) chứa tọa độ các hạt thức ăn
        - walls: tập hợp set chứa tọa độ các ô tường
        """
        self.start_pos = start_pos
        self.start_foods = frozenset(foods_set)
        # TỰ ĐỘNG CHUẨN HÓA: Hỗ trợ cả 2D grid lẫn set, tương thích cả True/False lẫn ký tự '%'
        if isinstance(walls, list):
            self.walls = {
                (x, y)
                for y, row in enumerate(walls)
                for x, is_wall in enumerate(row)
                if (is_wall is True or is_wall == '%')
            }
        else:
            self.walls = walls  # Nếu đã là set sẵn thì giữ nguyên

    def get_start_state(self):
        # Trạng thái xuất phát gồm: vị trí Pacman và toàn bộ thức ăn ban đầu
        return (self.start_pos, self.start_foods)

    def is_goal_state(self, state):
        # Đích đạt được khi tập thức ăn còn lại rỗng (đã ăn hết)
        pacman_pos, remaining_foods = state
        return len(remaining_foods) == 0

    def get_successors(self, state):
        successors = []
        pacman_pos, remaining_foods = state
        x, y = pacman_pos

        directions = [
            ('NORTH', (x, y - 1)),
            ('SOUTH', (x, y + 1)),
            ('EAST',  (x + 1, y)),
            ('WEST',  (x - 1, y))
        ]

        for action, next_pos in directions:
            # Nếu không đi vào tường
            if next_pos not in self.walls:
                # Nếu ô tiếp theo có thức ăn, loại hạt đó ra khỏi tập còn lại
                if next_pos in remaining_foods:
                    next_foods = remaining_foods - {next_pos}
                else:
                    next_foods = remaining_foods

                next_state = (next_pos, next_foods)
                step_cost = 1
                successors.append((next_state, action, step_cost))

        return successors

    def get_cost_of_actions(self, actions):
        return len(actions)
def food_heuristic(state, problem=None):
    """
    Heuristic cho FoodSearchProblem:
    Lấy khoảng cách Manhattan từ vị trí hiện tại của Pacman tới hạt thức ăn xa nhất.
    Đảm bảo tính Admissible vì để ăn hết thức ăn, Pacman tối thiểu phải đi tới hạt xa nhất.
    """
    pacman_pos, remaining_foods = state
    
    if not remaining_foods:
        return 0

    px, py = pacman_pos
    # Tìm khoảng cách Manhattan lớn nhất tới một hạt thức ăn bất kỳ còn lại
    max_distance = max(abs(px - fx) + abs(py - fy) for fx, fy in remaining_foods)
    return max_distance
class SearchAgent:
    """Agent điều khiển Pacman đi theo kết quả của thuật toán tìm kiếm."""
    def __init__(self, search_function, problem_class=PositionSearchProblem, heuristic=None, cost_fn=None):
        self.search_function = search_function
        self.problem_class = problem_class
        self.heuristic = heuristic
        self.cost_fn = cost_fn or (lambda x:1)
        self.actions = None  # Danh sách chuỗi hành động tìm được
        self.search_stats = None

    def get_action(self, state):
        # 1. Ở bước đầu tiên: chạy thuật toán tìm kiếm một lần duy nhất để tìm đường
        if self.actions is None:
            # Lấy vị trí đích là hạt thức ăn đầu tiên (nếu tìm 1 đích)
            # Hoặc truyền food_grid (nếu là FoodSearchProblem)
            start_pos = state.get_pacman_position()
            # Ví dụ tìm hạt mồi đầu tiên:
            #from evaluation import grid_positions( đã import ở đầu)
            foods = grid_positions(state.get_food())
            if self.problem_class == FoodSearchProblem:
                # FoodSearchProblem cần truyền tập hợp tất cả các hạt mồi
                problem = FoodSearchProblem(start_pos, foods, state.get_walls())
            else:
                # PositionSearchProblem chỉ cần 1 điểm đích (lấy hạt mồi đầu tiên)
                goal_pos = foods[0] if foods else start_pos
                problem = self.problem_class(start_pos, goal_pos, state.get_walls(), cost_fn=self.cost_fn)
            if self.heuristic:
                result = self.search_function(problem, self.heuristic)
            else:
                result = self.search_function(problem)
            self.search_stats = result
            if result["actions"] is None:
                self.actions = []
                print("[SearchAgent] Không tìm thấy đường đi tới đích!")
                return "Stop"
            self.actions = list(result["actions"])
        if len(self.actions) > 0:
            return self.actions.pop(0)

        # 3. Đã đi hết toàn bộ đường đi đã tìm được
        return "Stop"