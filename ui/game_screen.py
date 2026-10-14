import pygame

from ui.display import draw_game_screen
from ui.menu import load_font, FONT_MAIN, FONT_HEADING
from ui.display import build_wall_surface, draw_map, draw_hud, draw_p, draw_g, draw_box_winlose
from ui.pixel_assets import (
    COLORS, SIZE, LE_TREN, LE_DUOI,
    GHOST_RED, GHOST_PINK, GHOST_BLUE, GHOST_ORANGE,
    GHOST_ATE, GHOST_EAT,
)
from maps.map_generator import get_map

try:
    from src.engine import GameState
    from src.multiAgents import AlphaBetaAgent, ChaseGhost
    from src.search import (breadth_first_search, depth_first_search, 
                           uniform_cost_search, a_star_search, 
                           greedy_best_first_search, null_heuristic)
    from src.searchAgents import PositionSearchProblem, manhattan_heuristic, FoodSearchProblem, food_heuristic
except ImportError:
    from engine import GameState
    from multiAgents import AlphaBetaAgent, ChaseGhost
    from search import (breadth_first_search, depth_first_search, 
                        uniform_cost_search, a_star_search, 
                        greedy_best_first_search, null_heuristic)
    from searchAgents import PositionSearchProblem, manhattan_heuristic, FoodSearchProblem, food_heuristic

MODE_NAMES = {
    1: "Player vs AI Ghosts",
    2: "AI vs AI Autoplay",
    3: "Discovery Mode",
}
MAP_NAMES = {1: "Tiny Maze", 2: "Medium Maze", 3: "Big Maze", 4: "Unreachable Maze"}

ACTION_TO_DIR = {
    'NORTH': (0, -1),
    'SOUTH': (0, 1),
    'WEST': (-1, 0),
    'EAST': (1, 0),
    'STOP': (0, 0),
}

class ScreenLayout:
    """Adapter chuyển map_data của UI thành Layout tương thích GameState của Engine"""
    def __init__(self, map_data, pacman_pos, ghost_pos, cached_walls=None):
        self.pacman_start = tuple(pacman_pos)
        self.ghost_starts = [tuple(g) for g in ghost_pos]
        self.height = map_data.rows
        self.width = map_data.cols
        self.walls = cached_walls if cached_walls is not None else [[map_data.grid[r][c] == '%' for c in range(map_data.cols)] for r in range(map_data.rows)]
        self.food = [[map_data.grid[r][c] == '.' for c in range(map_data.cols)] for r in range(map_data.rows)]
        self.capsules = [(c, r) for r in range(map_data.rows) for c in range(map_data.cols) if map_data.grid[r][c] == 'o']

STEP_MS = 150
P_BLINK = 500
P_BLINKS = 3
MOVES = {
    pygame.K_UP: (0, -1),
    pygame.K_DOWN: (0, 1),
    pygame.K_LEFT: (-1, 0),
    pygame.K_RIGHT: (1, 0),
}

GHOST_ARTS = [GHOST_RED, GHOST_PINK, GHOST_BLUE, GHOST_ORANGE]
NORMAL, SCARED, EATEN = "NORMAL", "SCARED", "EATEN"
SCARED_SECONDS = {1: 4, 2: 5, 3: 6}
BLINK_MS = 1000
GHOST_POINTS = 200

class SearchProblemRecorder:
    """Wrapper bao ngoài SearchProblem để ghi nhận exploration_order cho animation
    mà tuyệt đối không cần thay đổi hay can thiệp vào mã nguồn gốc của src/search.py."""
    def __init__(self, problem):
        self._problem = problem
        self.exploration_order = []
        self._seen = set()

    def get_start_state(self):
        start = self._problem.get_start_state()
        pos = start[0] if (isinstance(start, tuple) and len(start) == 2 and isinstance(start[0], tuple)) else start
        if isinstance(pos, (tuple, list)) and len(pos) >= 2 and isinstance(pos[0], int):
            p = (int(pos[0]), int(pos[1]))
            if p not in self._seen:
                self._seen.add(p)
                self.exploration_order.append(p)
        return start

    def is_goal_state(self, state):
        pos = state[0] if (isinstance(state, tuple) and len(state) == 2 and isinstance(state[0], tuple)) else state
        if isinstance(pos, (tuple, list)) and len(pos) >= 2 and isinstance(pos[0], int):
            p = (int(pos[0]), int(pos[1]))
            if p not in self._seen:
                self._seen.add(p)
                self.exploration_order.append(p)
        return self._problem.is_goal_state(state)

    def get_successors(self, state):
        pos = state[0] if (isinstance(state, tuple) and len(state) == 2 and isinstance(state[0], tuple)) else state
        if isinstance(pos, (tuple, list)) and len(pos) >= 2 and isinstance(pos[0], int):
            p = (int(pos[0]), int(pos[1]))
            if p not in self._seen:
                self._seen.add(p)
                self.exploration_order.append(p)
        return self._problem.get_successors(state)

    def get_cost_of_actions(self, actions):
        return self._problem.get_cost_of_actions(actions)

    def __getattr__(self, name):
        return getattr(self._problem, name)


class GameScreen:
    def __init__(self):
        self.font_big = load_font(FONT_MAIN, 24)
        self.font_small = load_font(FONT_MAIN, 16)
        self.font_score = load_font(FONT_MAIN, 22)
        self.font_bigger = load_font(FONT_MAIN, 40)

        self.map_data = None
        self.wall_surf = None
        self.pacman_pos = [0, 0]
        self.pacman_dir = (1, 0)
        self.moving = False
        self.ghost_pos = []
        self.score = 0
        self.mode_text = ""
        self.map_text = ""
        self.last_step = 0

        self.status = "PLAYING"
        self.dying_start = 0
        self.font_heading = load_font(FONT_HEADING, 40)

        self.map_id = 1
        self.ghost_state = []
        self.ghost_path = []
        self.scared_end = 0
        self.eat_combo = 0

    def start(self, mode, map_id, algo=None, goal_type="single"):
        self.algo_name = algo or "astar"
        self.goal_type = goal_type or "single"
        self.search_stats = None
        self.search_actions = []
        self.planned_path = []

        self.map_data = get_map(mode, map_id)
        if self.map_data.p_start is None:
            raise ValueError("File map không có ký tự P (vị trí xuất phát của Pacman)")

        self.wall_surf = build_wall_surface(self.map_data)
        self.pacman_pos = list(self.map_data.p_start)
        self.pacman_dir = (1, 0)
        self.map_id = map_id
        self.score = 0
        self.mode_text = MODE_NAMES.get(mode, "Arcade")
        self.map_text = MAP_NAMES.get(map_id, "Custom Maze")
        self.cached_walls = [[self.map_data.grid[r][c] == '%' for c in range(self.map_data.cols)] for r in range(self.map_data.rows)]
        self.last_step = pygame.time.get_ticks()
        self.status = "PLAYING"
        self.paused = False # Trạng thái tạm dừng
        self.btn_pause_rect = None
        self.btn_restart_rect = None

        # Cấu hình AI: Mode 2 là Pacman AI tự chơi, Mode 1 là Người chơi vs Ma AI
        self.mode = mode
        self.is_ai_pacman = (mode == 2)
        if self.is_ai_pacman:
            self.pacman_agent = AlphaBetaAgent(depth=1)
            self.moving = True
        else:
            self.pacman_agent = None
            self.moving = False

        # CHẾ ĐỘ 3: TÌM ĐƯỜNG ĐI - LOẠI BỎ TOÀN BỘ MA THEO YÊU CẦU
        if self.mode == 3:
            self.ghost_pos = []
            self.ghost_state = []
            self.ghost_path = []
            self.ghost_agents = []
            self.scared_end = 0
            self.eat_combo = 0

            # LỌC MỒI THEO YÊU CẦU:
            # - Chế độ 1 mồi: Chỉ hiển thị duy nhất 1 mồi đích
            # - Chế độ nhiều mồi: Chỉ hiển thị 4-5 mồi rải rác ngẫu nhiên
            import random
            start_p = tuple(self.pacman_pos)
            all_existing_foods = [
                (c, r) for r in range(self.map_data.rows) for c in range(self.map_data.cols)
                if self.map_data.grid[r][c] in ('.', 'o')
            ]
            for c, r in all_existing_foods:
                self.map_data.grid[r][c] = ' '

            if self.goal_type == "single":
                if self.map_id == 4:
                    isolated = [p for p in all_existing_foods if p[0] >= 5]
                    target_food = isolated[0] if isolated else (7, 1)
                else:
                    target_food = max(
                        all_existing_foods,
                        key=lambda p: abs(p[0] - start_p[0]) + abs(p[1] - start_p[1])
                    )
                self.map_data.grid[target_food[1]][target_food[0]] = '.'
            else:
                if self.map_id == 4:
                    left_foods = [p for p in all_existing_foods if p[0] < 5]
                    right_foods = [p for p in all_existing_foods if p[0] >= 5]
                    chosen_foods = left_foods[:2] + right_foods[:2]
                else:
                    k = min(5, len(all_existing_foods))
                    chosen_foods = random.sample(all_existing_foods, k)
                for c, r in chosen_foods:
                    self.map_data.grid[r][c] = '.'

            # Chạy thuật toán tìm đường - lấy luôn exploration_order để animation
            self.search_stats = self._run_search()

            # ----- CÀI ĐẶT ANIMATION STATE MACHINE -----
            # explore_trace  : danh sách (x,y) theo thứ tự thuật toán đã mở rộng
            # explored_cells : tập ô đã hiển thị màu xanh (tăng dần khi animation)
            # path_cells     : danh sách ô đường đi màu vàng (hiện sau khi tìm xong)
            # search_phase   : "EXPLORING" -> "PATH_FOUND" -> "WALKING" -> "WIN"/"NO_PATH"
            # EXPLORE_BATCH_MS : ms mỗi lần tự động tiến 1 batch node khi auto
            # EXPLORE_BATCH_SIZE : số node hiện mỗi batch khi auto
            self.explore_trace = self.search_stats.get("exploration_order", [])
            self.explore_idx = 0
            self.explored_cells = set()

            if self.search_stats and self.search_stats.get("actions") is not None:
                # Tính toán đường đi màu vàng từ actions
                path_cells = []
                cur_x, cur_y = self.pacman_pos
                for act in self.search_stats["actions"]:
                    dx, dy = ACTION_TO_DIR.get(act, (0, 0))
                    cur_x += dx
                    cur_y += dy
                    path_cells.append((cur_x, cur_y))
                self.path_cells = path_cells
                self.search_actions = list(self.search_stats["actions"])
            else:
                self.path_cells = []
                self.search_actions = []

            self.planned_path = []  # Không dùng planned_path nữa (dùng path_cells thay thế)
            self.search_phase = "EXPLORING"
            self.moving = False
            self.paused = True      # Luôn bắt đầu ở trạng thái Pause

            self.EXPLORE_BATCH_MS = 120     # ms giữa các auto-step khi bật chạy
            self.EXPLORE_BATCH_SIZE = 2     # số node hiện mỗi tick auto (chậm)
            self.last_explore_tick = pygame.time.get_ticks()

        else:
            # Chế độ 1 và 2: Có ma săn đuổi
            self.ghost_pos = [list(pos) for pos in self.map_data.g_start]
            self.ghost_state = [NORMAL for _ in self.ghost_pos]
            self.ghost_path = [[] for _ in self.ghost_pos]
            self.scared_end = 0
            self.eat_combo = 0
            self.ghost_agents = [
                ChaseGhost(chase_prob=0.85, seed=i, index=i + 1)
                for i in range(len(self.ghost_pos))
            ]
            self.explore_trace = []
            self.explore_idx = 0
            self.explored_cells = set()
            self.path_cells = []
            self.search_phase = None

        # Đảm bảo cửa sổ không bị quá nhỏ khi chơi map cụt (10x4)
        width = max(self.map_data.cols * SIZE, 460)
        height = LE_TREN + max(self.map_data.rows * SIZE, 180) + LE_DUOI
        return pygame.display.set_mode((width, height))

    def get_game_state(self):
        """Chuyển đổi trạng thái màn hình hiện tại thành GameState để AI tính toán"""
        layout = ScreenLayout(self.map_data, self.pacman_pos, self.ghost_pos, self.cached_walls)
        state = GameState(layout)
        state.score = self.score
        now = pygame.time.get_ticks()
        if self.scared_end and now < self.scared_end:
            rem = max(1, int((self.scared_end - now) / 1000 * 2))
            state.scared_timers = [rem if s == SCARED else 0 for s in self.ghost_state]
        else:
            state.scared_timers = [0] * len(self.ghost_pos)
        return state

    def handle_event(self, event):
        # 1 BẮT PHÍM BẤM
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "BACK"

            # phím SPACE: bật/tắt tạm dừng, hoặc bắt đầu giai đoạn mới ở Mode 3
            elif event.key == pygame.K_SPACE:
                if self.mode == 3:
                    phase = getattr(self, 'search_phase', None)
                    if phase == "EXPLORING":
                        self.paused = not self.paused
                        if not self.paused:
                            self.last_explore_tick = pygame.time.get_ticks()
                    elif phase == "PATH_FOUND":
                        # Chuyển sang WALKING và bắt đầu đi
                        self.search_phase = "WALKING"
                        self.paused = False
                        self.last_step = pygame.time.get_ticks()
                    elif phase == "WALKING":
                        self.paused = not self.paused
                        if not self.paused:
                            self.last_step = pygame.time.get_ticks()
                else:
                    self.paused = not self.paused

            # phím R : restart
            elif event.key == pygame.K_r:
                self.start(self.mode, self.map_id,
                           getattr(self, 'algo_name', None),
                           getattr(self, 'goal_type', 'single'))

            # phím S: step 1 node (Mode 3) hoặc 1 bước game (Mode 1/2)
            elif event.key == pygame.K_s:
                if self.mode == 3:
                    phase = getattr(self, 'search_phase', None)
                    if phase == "EXPLORING":
                        self._advance_explore(1)
                    elif phase == "PATH_FOUND":
                        self.search_phase = "WALKING"
                        self.paused = True
                        self._step_walking()
                    elif phase == "WALKING" and self.status == "PLAYING":
                        self._step_walking()
                elif self.paused and self.status == "PLAYING":
                    self.step_once()

            # Nếu là chế độ người chơi (Mode != 2) thì nhận phím bấm
            elif not self.is_ai_pacman and event.key in MOVES:
                self.pacman_dir = MOVES[event.key]
                self.moving = True

        # 2 BẮT CLICK CHUỘT VÀO CÁC NÚT TRÊN MÀN HÌNH
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            # click pause / resume
            if self.btn_pause_rect and self.btn_pause_rect.collidepoint(mouse_pos):
                if self.mode == 3:
                    phase = getattr(self, 'search_phase', None)
                    if phase == "PATH_FOUND":
                        self.search_phase = "WALKING"
                        self.paused = False
                        self.last_step = pygame.time.get_ticks()
                    else:
                        self.paused = not self.paused
                        if not self.paused:
                            self.last_explore_tick = pygame.time.get_ticks()
                            self.last_step = pygame.time.get_ticks()
                else:
                    self.paused = not self.paused

            # click nút STEP
            elif self.btn_step_rect and self.btn_step_rect.collidepoint(mouse_pos):
                if self.mode == 3:
                    phase = getattr(self, 'search_phase', None)
                    if phase == "EXPLORING":
                        self._advance_explore(1)
                    elif phase == "PATH_FOUND":
                        self.search_phase = "WALKING"
                        self.paused = True
                        self._step_walking()
                    elif phase == "WALKING" and self.status == "PLAYING":
                        self._step_walking()
                elif self.paused and self.status == "PLAYING":
                    self.step_once()

            # Click nút RESTART
            elif self.btn_restart_rect and self.btn_restart_rect.collidepoint(mouse_pos):
                self.start(self.mode, self.map_id,
                           getattr(self, 'algo_name', None),
                           getattr(self, 'goal_type', 'single'))
        return None


    def can_go(self, direction):
        x = self.pacman_pos[0] + direction[0]
        y = self.pacman_pos[1] + direction[1]
        return self.map_data.cell(x, y) not in ('%', '-')

    def step_pacman(self):
        # 1. NẾU LÀ MODE 3 (TÌM KIẾM): Lấy từng bước từ đường đi đã tính sẵn
        if self.mode == 3:
            if self.search_actions:
                action = self.search_actions.pop(0)
                if self.planned_path:
                    self.planned_path.pop(0)
                if action in ACTION_TO_DIR:
                    self.pacman_dir = ACTION_TO_DIR[action]
                    self.moving = True
            else:
                self.moving = False # Đã đi tới đích

        # 2. NẾU LÀ MODE 2 (ĐỐI KHÁNG AI): Hỏi AlphaBeta nước đi tối ưu
        elif self.is_ai_pacman:
            state = self.get_game_state()
            action = self.pacman_agent.get_action(state)
            if action and action in ACTION_TO_DIR and action != 'STOP':
                self.pacman_dir = ACTION_TO_DIR[action]
                self.moving = True
            else:
                self.moving = False

        if not self.moving:
            return
            
        if self.can_go(self.pacman_dir):
            self.pacman_pos[0] += self.pacman_dir[0]
            self.pacman_pos[1] += self.pacman_dir[1]
            x, y = self.pacman_pos

            # Chỉ phạt trừ điểm khi Pacman bước vào ô bùn lầy '~'
            if self.map_data.cell(x, y) == '~':
                self.score -= 5  # Bị phạt 3 điểm vì lội bùn
                
            if self.map_data.cell(x, y) == 'o':
                self.start_scared()
            self.score += self.map_data.eat(x, y)
            self.check_collision()

            # Nếu là Mode 3 và đã đi hết lộ trình: Báo Thắng!
            if self.mode == 3 and len(self.search_actions) == 0:
                self.moving = False
                self.status = "WIN"

    def start_scared(self):
        """Pacman vừa ăn goal1: ma NORMAL -> SCARED, đếm giờ lại từ đầu."""
        self.scared_end = pygame.time.get_ticks() + SCARED_SECONDS[self.map_id] * 1000
        self.eat_combo = 0
        for i in range(len(self.ghost_state)):
            if self.ghost_state[i] == NORMAL:    # ma đang EATEN thì cứ về nhà tiếp
                self.ghost_state[i] = SCARED

    def update_scared(self, now):
        """Hết giờ thì mọi ma SCARED trở lại NORMAL."""
        if self.scared_end and now >= self.scared_end:
            self.scared_end = 0
            for i in range(len(self.ghost_state)):
                if self.ghost_state[i] == SCARED:
                    self.ghost_state[i] = NORMAL

    def check_collision(self):
        """Pacman và ma ở cùng một ô."""
        for i, pos in enumerate(self.ghost_pos):
            if pos != self.pacman_pos:
                continue
            if self.ghost_state[i] == SCARED:
                self.eat_combo += 1
                self.score += GHOST_POINTS * self.eat_combo      # 200, 400, 600
                self.ghost_state[i] = EATEN
                home = self.map_data.g_start[i]                  # ô xuất phát của chính con ma đó
                self.ghost_path[i] = self.map_data.find_path(tuple(pos), home)
            # elif NORMAL: ma bắt được Pacman -> xử lý thua (làm sau)

    def step_eaten_ghosts(self):
        """Mỗi bước, ma EATEN đi 1 ô trên đường về nhà; tới nơi thì thành NORMAL."""
        for i, state in enumerate(self.ghost_state):
            if state != EATEN:
                continue
            if self.ghost_path[i]:
                x, y = self.ghost_path[i].pop(0)
                self.ghost_pos[i] = [x, y]
            if not self.ghost_path[i]:
                self.ghost_state[i] = NORMAL

    def ghost_art(self, i, now):
        """Chọn hình vẽ cho con ma thứ i."""
        normal_art = GHOST_ARTS[i % len(GHOST_ARTS)]
        state = self.ghost_state[i]
        if state == EATEN:
            return GHOST_ATE
        if state == SCARED:
            remaining = self.scared_end - now
            if remaining <= BLINK_MS:
                # chia 1 giây cuối thành 6 khoảng: EAT, thường, EAT, thường, EAT, thường
                phase = (BLINK_MS - remaining) * 6 // BLINK_MS
                if phase % 2 == 1:
                    return normal_art
            return GHOST_EAT
        return normal_art

    def check_end(self):
        """Gọi sau MỖI lần Pacman hoặc ma di chuyển."""
        px, py = self.pacman_pos
        """""if any((g[0], g[1]) == (px, py) for g in self.ghost_pos):   # thua xét trước
            self.status = "DYING"""
        #ban đầu ăn ma là chết luôn dù đang ở trạng thái gì , đã saurw thành ăn ma ở trạng thái normal mới chít
        px, py = self.pacman_pos
        #chỉ bị ma bắt nếu ở trạng thái normal
        is_caught = any((g[0], g[1]) == (px, py) and self.ghost_state[i] == NORMAL 
        for i, g in enumerate(self.ghost_pos))
        if is_caught:
            self.status = "DYING"
            self.dying_start = pygame.time.get_ticks()
        elif self.map_data.goal_left() == 0:
            self.status = "WIN"
    
    def update(self):
        now = pygame.time.get_ticks()

        # ---- CHẾ ĐỘ 3: State machine animation tìm đường ----
        if self.mode == 3:
            if self.status != "PLAYING":
                return
            if self.paused:
                return
            phase = getattr(self, 'search_phase', None)
            if phase == "EXPLORING":
                if now - self.last_explore_tick >= self.EXPLORE_BATCH_MS:
                    self.last_explore_tick = now
                    self._advance_explore(self.EXPLORE_BATCH_SIZE)
            elif phase == "WALKING":
                if now - self.last_step >= STEP_MS:
                    self.last_step = now
                    self._step_walking()
            return  # Bỏ qua logic update bình thường của Mode 1/2

        # ---- CHẾ ĐỘ 1 & 2: Logic thông thường ----
        self.update_scared(now)
        if self.status == "DYING":                    # đang nhấp nháy
            if now - self.dying_start >= P_BLINKS * 2 * P_BLINK:
                self.status = "LOSE"
            return
        if self.status != "PLAYING":
            return
        #Nếu đang dừng thì ko tự động đi bước tiếp thep
        if self.paused:
            return
        if now - self.last_step < STEP_MS:
            return
        self.last_step = now
        self.step_once() #gọi hàm 1 bước ở dưới

        
    def step_once(self):
        """Thực hiện 1 bước của pacman và ghost"""
        if self.status != "PLAYING":                  # WIN / LOSE: đứng yên
            return
        self.step_pacman()
        self.step_eaten_ghosts()
        self.step_ghosts()
        self.check_collision()
        self.check_end()

    def _advance_explore(self, n):
        """Tiến thêm n node vào explored_cells (animation xanh nhạt ở Mode 3)."""
        for _ in range(n):
            if self.explore_idx < len(self.explore_trace):
                self.explored_cells.add(self.explore_trace[self.explore_idx])
                self.explore_idx += 1
            else:
                # Hết trace → chuyển trạng thái
                if self.path_cells:
                    self.search_phase = "PATH_FOUND"
                    self.paused = True  # Dừng lại để người dùng thấy đường màu vàng
                else:
                    self.search_phase = "NO_PATH"
                    self.status = "NO_PATH"
                break

    def _step_walking(self):
        """Di chuyển Pacman 1 bước theo đường đã tìm được (Mode 3 - WALKING phase)."""
        if self.search_actions:
            action = self.search_actions.pop(0)
            # Bỏ ô đầu path_cells vì Pacman đã đến đó
            if self.path_cells:
                self.path_cells.pop(0)
            if action in ACTION_TO_DIR:
                dx, dy = ACTION_TO_DIR[action]
                self.pacman_dir = (dx, dy)
                self.moving = True
                # Di chuyển Pacman
                if self.can_go(self.pacman_dir):
                    self.pacman_pos[0] += dx
                    self.pacman_pos[1] += dy
                    x, y = self.pacman_pos
                    self.score += self.map_data.eat(x, y)
            if not self.search_actions:
                self.status = "WIN"
        else:
            self.status = "WIN"

    def step_ghosts(self):
        """Cho ma AI bước đi: dùng ChaseGhost từ multiAgents khi bình thường, né Pacman khi sợ"""
        if self.mode == 3:
            return  # Tuyệt đối không có ma di chuyển trong Chế độ Tìm đường

        state = self.get_game_state()
        import random
        for i, g_state in enumerate(self.ghost_state):
            if g_state == EATEN:
                continue
            gx, gy = self.ghost_pos[i]
            legal_moves = []
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                if self.map_data.cell(gx + dx, gy + dy) != '%':
                    legal_moves.append((dx, dy))
            if not legal_moves:
                continue

            if g_state == SCARED:
                # Khi ma sợ: cố gắng chạy xa khỏi Pacman
                px, py = self.pacman_pos
                best_moves = []
                max_d = -1
                for dx, dy in legal_moves:
                    d = abs(gx + dx - px) + abs(gy + dy - py)
                    if d > max_d:
                        max_d = d
                        best_moves = [(dx, dy)]
                    elif d == max_d:
                        best_moves.append((dx, dy))
                chosen = random.choice(best_moves)
                self.ghost_pos[i] = [gx + chosen[0], gy + chosen[1]]
            else:
                # Khi bình thường: Ma dùng ChaseGhost từ multiAgents.py để săn đuổi Pacman!
                moved = False
                if i < len(self.ghost_agents):
                    g_action = self.ghost_agents[i].get_action(state, agent_index=i + 1)
                    if g_action in ACTION_TO_DIR:
                        dx, dy = ACTION_TO_DIR[g_action]
                        if (dx, dy) in legal_moves:
                            self.ghost_pos[i] = [gx + dx, gy + dy]
                            moved = True
                if not moved:
                    chosen_dx, chosen_dy = random.choice(legal_moves)
                    self.ghost_pos[i] = [gx + chosen_dx, gy + chosen_dy]

    def draw(self, screen):
        self.btn_pause_rect, self.btn_step_rect, self.btn_restart_rect = draw_game_screen(screen, self)


    def _run_search(self):
        """
        Đóng gói việc gọi các thuật toán tìm kiếm từ src/search.py
        Hỗ trợ 2 chế độ:
          - Ăn 1 mồi (PositionSearchProblem)
          - Ăn nhiều mồi (FoodSearchProblem)
        Hỗ trợ cả Map cụt không có đường đi (map_id == 4).
        """
        start_pos = tuple(self.pacman_pos)
        current_foods = [
            (c, r) for r in range(self.map_data.rows) for c in range(self.map_data.cols) 
            if self.map_data.grid[r][c] in ('.', 'o')
        ]

        if self.goal_type == "multi":
            raw_problem = FoodSearchProblem(start_pos, set(current_foods), self.map_data.grid)
            heuristic = food_heuristic
        else:
            goal_pos = tuple(current_foods[0]) if current_foods else start_pos
            raw_problem = PositionSearchProblem(start_pos, goal_pos, self.map_data.grid)
            heuristic = manhattan_heuristic

        recorder = SearchProblemRecorder(raw_problem)

        algos = {
            "bfs": lambda: breadth_first_search(recorder),
            "dfs": lambda: depth_first_search(recorder),
            "ucs": lambda: uniform_cost_search(recorder),
            "greedy": lambda: greedy_best_first_search(recorder, heuristic),
            "astar": lambda: a_star_search(recorder, heuristic)
        }
        res = algos.get(self.algo_name, algos["astar"])()
        res["exploration_order"] = recorder.exploration_order
        return res
