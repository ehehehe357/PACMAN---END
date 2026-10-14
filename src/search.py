try:
    from src.util import Stack, Queue, PriorityQueue
except ImportError:
    from util import Stack, Queue, PriorityQueue
# Ban đầu viết from util import S , Q , PQ chỉ chạy được khi đứng trực tiếp trong thư mục src/.Nếu đứng ở thử mục gốc thì tịt.
import time
class SearchProblem:
    """
    Lớp trừu tượng định nghĩa cấu trúc của một bài toán tìm kiếm.
    Các lớp bài toán cụ thể (như PositionSearchProblem, FoodSearchProblem) 
    sẽ kế thừa từ lớp này và hiện thực hóa các phương thức bên dưới.
    """

    def get_start_state(self):
        """
        Trả về trạng thái bắt đầu của bài toán tìm kiếm.
        Ví dụ: 
          - Với bài toán 1 đích: trả về tọa độ (x, y).
          - Với bài toán nhiều thức ăn: trả về ((x, y), remaining_food).
        """
        raise NotImplementedError("Phương thức get_start_state chưa được cài đặt!")

    def is_goal_state(self, state):
        """
        Nhận vào một trạng thái (state).
        Trả về True nếu trạng thái đó là trạng thái đích, ngược lại trả về False.
        """
        raise NotImplementedError("Phương thức is_goal_state chưa được cài đặt!")

    def get_successors(self, state):
        """
        Nhận vào một trạng thái (state).
        Trả về danh sách các bộ 3 phần tử:
            [(next_state, action, step_cost), ...]
            
        Trong đó:
          - next_state: trạng thái kế tiếp hợp lệ (không đi xuyên tường).
          - action: chuỗi hành động di chuyển ('North', 'South', 'East', 'West').
          - step_cost: chi phí của bước đi đó (mặc định là 1 nếu chi phí đồng nhất).
        """
        raise NotImplementedError("Phương thức get_successors chưa được cài đặt!")

    def get_cost_of_actions(self, actions):
        """
        Nhận vào danh sách các hành động: ['North', 'East', ...]
        Trả về tổng chi phí để thực hiện chuỗi hành động đó.
        Nếu chuỗi hành động không hợp lệ, trả về vô cùng (float('inf')).
        """
        raise NotImplementedError("Phương thức get_cost_of_actions chưa được cài đặt!")
def breadth_first_search(problem):
    start_time = time.time()
    start_state = problem.get_start_state()
    nodes_expanded = 0
    frontier = Queue()
    frontier.push((start_state,[]))
    visited = {start_state}
    while not frontier.is_empty():
        state,actions = frontier.pop()
        if problem.is_goal_state(state):
            return {
                "actions" : actions,
                "total_cost" : problem.get_cost_of_actions(actions),
                "nodes_expanded" : nodes_expanded,
                "execution_time" : time.time() - start_time
            }
        nodes_expanded += 1
        for next_state,action,step_cost in problem.get_successors(state):
            if next_state not in visited:
                visited.add(next_state)
                frontier.push((next_state, actions + [action]))
    return{
        "actions" : None,
        "total_cost" : 0,
        "nodes_expanded" : nodes_expanded,
        "execution_time" : time.time() - start_time
    }
def depth_first_search(problem):
    start_time = time.time()
    nodes_expanded = 0
    start_state = problem.get_start_state()
    frontier = Stack()
    frontier.push((start_state,[]))
    visited = set()
    while not frontier.is_empty():
        state,actions = frontier.pop()
        if problem.is_goal_state(state):
            return{
                "actions" : actions,
                "total_cost" : problem.get_cost_of_actions(actions),
                "nodes_expanded" : nodes_expanded,
                "execution_time" : time.time() - start_time
            }
        if state not in visited:
            visited.add(state)
            nodes_expanded += 1
            for next_state,action,step_cost in problem.get_successors(state):
                if next_state not in visited:
                    frontier.push((next_state, actions + [action]))
    return{
        "actions" : None,
        "total_cost" : 0,
        "nodes_expanded" : nodes_expanded,
        "execution_time" : time.time() - start_time
    }
def uniform_cost_search(problem):
    start_time = time.time()
    nodes_expanded = 0
    frontier = PriorityQueue()
    start_state = problem.get_start_state()
    frontier.push((start_state,[],0),0)
    explored_costs = {}
    while not frontier.is_empty():
        state,actions,current_cost = frontier.pop()
        if problem.is_goal_state(state):
            return{
                "actions" : actions,
                "total_cost" : current_cost,
                "nodes_expanded" : nodes_expanded,
                "execution_time" : time.time() - start_time
            }
        if state not in explored_costs or current_cost < explored_costs[state]:
            explored_costs[state] = current_cost
            nodes_expanded += 1
            for next_state,action,step_cost in problem.get_successors(state):
                new_cost = current_cost + step_cost
                if next_state not in explored_costs or new_cost < explored_costs[next_state]:
                    frontier.push((next_state, actions + [action], new_cost), new_cost)
    return {
        "actions" : None,
        "total_cost" : 0,
        "nodes_expanded" : nodes_expanded,
        "execution_time" : time.time() - start_time
    }
def null_heuristic(state, problem=None):
    return 0
def a_star_search(problem, heuristic = null_heuristic):
    start_time = time.time()
    nodes_expanded = 0
    start_state = problem.get_start_state()
    frontier = PriorityQueue()
    initial_f = 0 + heuristic(start_state,problem)
    frontier.push((start_state, [], 0), initial_f)
    explored_costs = {}
    while not frontier.is_empty():
        state, actions, g_cost = frontier.pop()
        if problem.is_goal_state(state):
            return{
                "actions" : actions,
                "total_cost" : g_cost,
                "nodes_expanded" : nodes_expanded,
                "execution_time" : time.time() - start_time
            }
        if state not in explored_costs or g_cost < explored_costs[state]:
            explored_costs[state] = g_cost
            nodes_expanded +=1
            for next_state, action, step_cost in problem.get_successors(state):
                new_cost = g_cost + step_cost
                if next_state not in explored_costs or new_cost < explored_costs[next_state]:
                    f_cost = new_cost + heuristic(next_state,problem)
                    frontier.push((next_state, actions + [action], new_cost), f_cost)
    return {
        "actions" : None,
        "total_cost" : 0,
        "nodes_expanded" : nodes_expanded,
        "execution_time" : time.time() - start_time
    }
def greedy_best_first_search(problem,heuristic = null_heuristic):
    start_time = time.time()
    start_state = problem.get_start_state()
    nodes_expanded = 0
    frontier = PriorityQueue()
    initial_h = heuristic(start_state,problem)
    frontier.push((start_state,[],0),initial_h)
    explored = set()
    while not frontier.is_empty():
        state,actions,g_cost = frontier.pop()
        if problem.is_goal_state(state):
            return{
                "actions" : actions,
                "total_cost" : g_cost,
                "nodes_expanded" : nodes_expanded,
                "execution_time" : time.time() - start_time
            }
        if state not in explored:
            explored.add(state)
            nodes_expanded += 1
            for next_state,action,step_cost in problem.get_successors(state):
                if next_state not in explored:
                    new_cost = g_cost + step_cost
                    h_cost = heuristic(next_state,problem)
                    frontier.push((next_state, actions + [action], new_cost), h_cost)
    return{
        "actions" : None,
        "total_cost" : 0,
        "nodes_expanded" : nodes_expanded,
        "execution_time" : time.time() - start_time
    }
