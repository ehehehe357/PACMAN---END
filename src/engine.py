import copy

class GameState:
    """
    Lớp GameState đóng vai trò là 'nguồn dữ liệu chân lý' duy nhất kết nối 
    giữa Game Engine (Pygame) và các thuật toán AI (Search AI, Minimax, Expectimax).
    """

    def __init__(self, layout):
        if layout is None:
            raise ValueError("Layout ko được để trống đâu cưng")
        
        
        # Khởi tạo trạng thái game dựa trên layout (bản đồ đọc từ maps.txt).
        
        self.pacman_pos = layout.pacman_start      
        self.ghost_positions = list(layout.ghost_starts)
        self.ghost_starts = list(layout.ghost_starts)  # Lưu vị trí xuất phát để hồi sinh ma khi bị ăn
        self.scared_timers = [0] * len(self.ghost_positions)  # Bộ đếm thời gian sợ của từng con ma
        self.food_grid = layout.food
        layout.food               # Grid 2D chứa Bool (True là có mồi)
        self.walls = layout.walls                  # Grid 2D chứa Bool (True là tường)
        self.capsules = layout.capsules            # List [(x, y)...]
        self.score = 0                             # Điểm số hiện tại
        self.win = False                           # Trạng thái Thắng
        self.lose = False                          # Trạng thái Thua

    # =========================================================================
    # 1. NHÓM HÀM TRUY VẤN THÔNG TIN BẢN ĐỒ VÀ VỊ TRÍ
    # =========================================================================

    def get_pacman_position(self):
        """Trả về tọa độ dạng tuple (x, y) hiện tại của Pacman."""
        return self.pacman_pos

    def get_ghost_positions(self):
        """Trả về danh sách tọa độ các con Ma: [(x1, y1), (x2, y2), ...]."""
        return self.ghost_positions

    def get_food(self):
        """Trả về ma trận Grid 2D chứa vị trí các hạt mồi (True nếu còn mồi)."""
        return self.food_grid

    def get_walls(self):
        """Trả về ma trận Grid 2D chứa vị trí các bức tường (True nếu là tường)."""
        return self.walls

    def get_capsules(self):
        """Trả về danh sách các viên năng lượng to (Capsules)."""
        return self.capsules

    def get_num_food(self):
        """Trả về tổng số hạt mồi còn lại trên bàn chơi."""
        # Giả sử food_grid có phương thức count() hoặc tính từ danh sách
        return sum(row.count(True) for row in self.food_grid)
    
    def get_num_agents(self):
        """trả về tổng số agent có trên bàn chơi"""
        return 1 + len(self.ghost_positions)

    def get_ghost_scared_timers(self):
        """Trả về danh sách thời gian sợ còn lại của các con ma."""
        return self.scared_timers

    def is_ghost_scared(self, ghost_index):
        """Trả về True nếu con ma thứ ghost_index (0-indexed) đang sợ."""
        if 0 <= ghost_index < len(self.scared_timers):
            return self.scared_timers[ghost_index] > 0
        return False

    # =========================================================================
    # 2. NHÓM HÀM LOGIC QUYẾT ĐỊNH VÀ GIẢ LẬP TƯƠNG LAI
    # =========================================================================

    def get_legal_actions(self, agent_index=0):
        """
        Trả về danh sách các nước đi hợp lệ không bị vướng tường.
        agent_index = 0: Pacman
        agent_index >= 1: Con Ma tương ứng
        """
        # 1. Nếu game đã thắng hoặc thua -> trả về []
        if self.win or self.lose:
            return []
        # 2. Lấy vị trí hiện tại của agent (Pacman hoặc Ma)
        if agent_index == 0:
            current_pos = self.pacman_pos
        else:
            # kiểm tra xem ma index có hợp lệ ko
            ghost_index = agent_index - 1
            if ghost_index < len(self.ghost_positions):
                current_pos = self.ghost_positions[ghost_index]
            else:
                return []  

        # 3. Kiểm tra 4 hướng xung quanh ('NORTH', 'SOUTH', 'WEST', 'EAST') xem có bị vướng tường ko
        legal_actions = []
        # 4 hướng đi chính
        directions = {
            'NORTH': (0, -1),
            'SOUTH': (0, 1),
            'WEST': (-1, 0),
            'EAST': (1, 0)
        }
        x ,y= current_pos
        for action, (dx, dy) in directions.items():
            next_x,next_y = x + dx , y + dy

            num_rows = len(self.walls)
            num_cols = len(self.walls[0])
            if 0 <= next_x < num_cols and 0 <= next_y < num_rows: # kiểm tra xem có nằm trong biên ko
                if not self.walls[next_y][next_x]:  # Kiểm tra xem có phải tường ko
                    legal_actions.append(action)
        return legal_actions




    def generate_successor(self, agent_index, action,apply_penalty=True):
        """
        HÀM GIẢ LẬP TƯƠNG LAI (CỰC KỲ QUAN TRỌNG):
        Tạo và trả về một đối tượng GameState HOÀN TOÀN MỚI thể hiện bàn chơi 
        sau khi nhân vật agent_index thực hiện nước đi action.
        """
        legal_actions = self.get_legal_actions(agent_index)
        if action not in legal_actions:
            raise ValueError(f" Hành động {action} không hợp lệ cho agent {agent_index} tại vị trí hiện tại đâu nha.")
        # 1. Tạo bản sao sâu (deepcopy) để không làm ảnh hưởng bàn chơi thật
        successor = copy.deepcopy(self)
        # 2. Cập nhật vị trí mới cho nhân vật (Pacman hoặc Ma)
        if agent_index == 0:
            # vị trí mới của pacman
            old_pos = successor.pacman_pos
            new_pos = self._get_next_position(old_pos, action)
            successor.pacman_pos = new_pos

            # trừ điểm sau 1 bước đi
            if apply_penalty:
                successor.score -= 1

            #khi pacman ăn mồi
            x, y = new_pos
            if successor.food_grid[y][x]:
                successor.food_grid[y][x] = False # ăn mồi rồi nên bỏ mồi khỏi ô đó
                successor.score += 10 # cộng điểm ăn mồi

            # khi pacman ăn capsule
            if new_pos in successor.capsules:
                successor.capsules.remove(new_pos) # bỏ capsule khỏi danh sách
                successor.score += 50 # cộng điểm ăn capsule
                # Kích hoạt trạng thái sợ cho toàn bộ ma (40 bước đi)
                SCARED_TIME = 40
                successor.scared_timers = [SCARED_TIME] * len(successor.ghost_positions)

        else:
            # vị trí mới của ma
            ghost_idx = agent_index - 1
            old_pos = successor.ghost_positions[ghost_idx]
            new_pos = self._get_next_position(old_pos, action)
            successor.ghost_positions[ghost_idx] = new_pos
            # Giảm thời gian sợ của con ma này đi 1 bước
            if successor.scared_timers[ghost_idx] > 0:
                successor.scared_timers[ghost_idx] -= 1
        
        # 3. Kiểm tra điều kiện Va chạm / Thắng / Thua (_update_win_lose_status)
        successor._update_win_lose_status()

        return successor

    # =========================================================================
    # 3. NHÓM HÀM TRẠNG THÁI GAME & TRỌNG TÀI
    # =========================================================================

    def get_score(self):
        """Trả về điểm số hiện tại của game."""
        return self.score

    def is_win(self):
        """Trả về True nếu Pacman đã ăn hết mồi."""
        return self.win

    def is_lose(self):
        """Trả về True nếu Pacman bị Ma bắt."""
        return self.lose

    # =========================================================================
    # HÀM BỔ TRỢ NỘI BỘ
    # =========================================================================

    def _get_next_position(self, current_pos, action):
        #tính tọa độ tiếp theo
        x,y= current_pos
        directions = {
            'NORTH': (0, -1),
            'SOUTH': (0, 1),
            'WEST': (-1, 0),
            'EAST': (1, 0)
        }
        if action in directions:
            dx, dy = directions[action]
            return (x + dx, y + dy)

        return current_pos  # Nếu action không hợp lệ, giữ nguyên vị trí.

    def _update_win_lose_status(self):
        # 1. Kiểm tra Pacman đụng độ Ma
        if not self.lose:
            for i, ghost_pos in enumerate(self.ghost_positions):
                if self.pacman_pos == ghost_pos:
                    if self.scared_timers[i] > 0:
                        # Ma đang sợ: Pacman ăn được ma!
                        self.score += 200  # Cộng 200 điểm
                        self.scared_timers[i] = 0  # Con ma này hết sợ
                        # Đưa ma về vị trí xuất phát ban đầu
                        self.ghost_positions[i] = self.ghost_starts[i]
                    else:
                        # Ma bình thường: Pacman bị bắt -> Thua
                        self.lose = True
                        self.score -= 500
                        return

    # 2. Kiểm tra ăn hết mồi -> Thắng
        if not self.win and not self.lose:
            has_food = any(True in row for row in self.food_grid)
            if not has_food and len(self.capsules) == 0:
                self.win = True
                self.score += 500

class Game:
    """ Class điều phối và chứa vòng lặp của game """
    def __init__(self, agents, display,initial_state):
        self.agents = agents   # Danh sách các agent (Pacman và Ma)
        self.display = display  # Hiển thị game (Pygame)
        self.state = initial_state  #game ban đầu

        self.game_over =False  # Cờ kết thúc game

    def run(self):
        """ vòng lặp chính của game"""
        self.display.initialize(self.state)  # Khởi tạo hiển thị game
        agent_index = 0     #bắt đầu ván đấu,lượt đầu tiên luôn là của pacman
        num_agents = len(self.agents) # tổng số agent (Pacman + Ma)


        while not self.game_over:
            # Lấy agent hiện tại dựa trên agent_index
            current_agent = self.agents[agent_index]

            # hỏi agent xem hướng đi nào tối ưu nhất

            action = current_agent.get_action(self.state)
            if action is None:
                self.game_over = True
                break
            is_human = getattr(current_agent, 'is_human', False)
            penalty = not is_human  # Nếu là người chơi, không áp dụng trừ điểm

            # cập nhật trạng thái mới
            self.state = self.state.generate_successor(agent_index, action, apply_penalty=penalty)

            # vẽ lại giao diện game
            self.display.update(self.state)

            # kiểm tra kết thúc game
            if self.state.is_win() or self.state.is_lose():
                self.game_over = True
                break

            # chuyển lượt cho agent tiếp theo
            agent_index = (agent_index + 1) % num_agents

        