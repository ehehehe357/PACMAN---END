
import pygame
from ui.pixel_assets import (
    COLORS, P_OPEN, P_CLOSED, GOAL1, GOAL2, SIZE, LE_TREN, LE_DUOI
)
BLINK_MS = 1000
p_couter = 0
p_speed = 10
is_mouth_open = True

WALL_T = 4

def surface_matrix (matrix, pixel_scale=4):
    rows = len(matrix)
    cols = len(matrix[0])

    width = cols*pixel_scale
    height = rows*pixel_scale

    P = pygame.Surface((width, height), pygame.SRCALPHA)

    for r_idx, row in enumerate(matrix):
        for c_idx, char in enumerate(row):
            if char in COLORS and COLORS[char]:
                color = COLORS[char]
                pygame.draw.rect(
                    P,
                    color,
                    (
                        c_idx * pixel_scale,
                        r_idx * pixel_scale,
                        pixel_scale,
                        pixel_scale
                    )
                )
    return P

p_open = surface_matrix(P_OPEN)
p_close = surface_matrix(P_CLOSED)
DIR_ANGLE = {(1, 0): 0, (0, -1): 90, (-1, 0): 180, (0, 1): 270}
p_open_dir = {d: pygame.transform.rotate(p_open, a) for d, a in DIR_ANGLE.items()}
p_close_dir = {d: pygame.transform.rotate(p_close, a) for d, a in DIR_ANGLE.items()}
goal1_surf = surface_matrix(GOAL1, pixel_scale=6)
goal2_surf = surface_matrix(GOAL2, pixel_scale=6)
_ghost_cache = {}
_mud_txt_surf = None

def blit_center(screen, surf, col, row):
    """Vẽ surf vào chính giữa ô (col, row)."""
    x = col * SIZE + (SIZE - surf.get_width()) // 2
    y = row * SIZE + LE_TREN + (SIZE - surf.get_height()) // 2
    screen.blit(surf, (x, y))

def draw_p (screen, potision, direction=(1, 0)):
    global p_couter, is_mouth_open
    x, y = potision
    #pos_x = int (x*SIZE)
    #pos_y = int(y*SIZE + LE_TREN)

    p_couter +=1
    if p_couter >= p_speed:
        is_mouth_open = not is_mouth_open
        p_couter = 0

    sprites = p_open_dir if is_mouth_open else p_close_dir

    #current_art = p_open if is_mouth_open else p_close
    #screen.blit(current_art, (pos_x, pos_y))
    blit_center(screen, sprites.get(direction, sprites[(1, 0)]), x, y)

def draw_g (screen, position, ghost_art):
    x, y = position
    pos_x = int (x*SIZE)
    pos_y = int (y*SIZE + LE_TREN)

    g_surf = surface_matrix(ghost_art, pixel_scale=4)
    screen.blit(g_surf, (pos_x, pos_y))

def build_wall_surface(map_data):
    """Vẽ tường 1 lần duy nhất ra 1 Surface, mỗi frame chỉ blit lại."""
    surf = pygame.Surface((map_data.cols * SIZE, map_data.rows * SIZE), pygame.SRCALPHA)
    color = COLORS['BL']
    t = WALL_T

    for r in range(map_data.rows):
        for c in range(map_data.cols):
            x, y = c * SIZE, r * SIZE

            if not map_data.is_wall(c, r):
                if map_data.grid[r][c] == '-':
                    pygame.draw.rect(surf, COLORS['P'], (x, y + SIZE // 2 - t // 2, SIZE, t))
                continue

            if r > 0 and not map_data.is_wall(c, r - 1):
                pygame.draw.rect(surf, color, (x, y, SIZE, t))
            if r < map_data.rows - 1 and not map_data.is_wall(c, r + 1):
                pygame.draw.rect(surf, color, (x, y + SIZE - t, SIZE, t))
            if c > 0 and not map_data.is_wall(c - 1, r):
                pygame.draw.rect(surf, color, (x, y, t, SIZE))
            if c < map_data.cols - 1 and not map_data.is_wall(c + 1, r):
                pygame.draw.rect(surf, color, (x + SIZE - t, y, t, SIZE))
    return surf


def draw_map(screen, map_data, wall_surf):
    screen.blit(wall_surf, (0, LE_TREN))
    for r in range(map_data.rows):
        for c in range(map_data.cols):
            ch = map_data.grid[r][c]
            x = c * SIZE
            y = r * SIZE + LE_TREN
            
            # Vẽ ô bùn lầy '~' có viền và đánh dấu chi phí = 5
            if ch == '~':
                mud_rect = pygame.Rect(x + 2, y + 2, SIZE - 4, SIZE - 4)
                pygame.draw.rect(screen, COLORS['MUD'], mud_rect, border_radius=4)
                # Vẽ nhãn số 5 nhỏ
                global _mud_txt_surf
                if _mud_txt_surf is None:
                    _font_mini = pygame.font.SysFont("arial", 12, bold=True)
                    _mud_txt_surf = _font_mini.render("5", True, COLORS['MUD_TXT'])
                screen.blit(_mud_txt_surf, _mud_txt_surf.get_rect(center=mud_rect.center))
            elif ch == 'o':
                blit_center(screen, goal1_surf, c, r)
            elif ch == '.':
                blit_center(screen, goal2_surf, c, r)

def draw_hud(screen, map_data, mode, mode_text, map_text, score, 
             font_big, font_small, font_score, 
             search_stats=None, algo_name=None, agent_stats=None, game_obj=None):
    """Vẽ thanh thông số HUD ở dải trên màn hình theo đúng Mục 4 của đề bài."""
    top_y1 = 4
    top_y2 = 28
    top_y3 = 48
    
    # 1. Chế độ 3: Tìm kiếm đường đi (Search)
    if mode == 3:
        algo_title = (algo_name or "A*").upper()
        success = search_stats and (search_stats.get("actions") is not None)
        status_txt = "FOUND" if success else "NO SOLUTION"
        status_color = COLORS['G'] if success else COLORS['R']

        # Dòng 1: Tên thuật toán + Trạng thái
        s_left = font_big.render(f"SEARCH: {algo_title} ({map_text})", True, COLORS['Y'])
        s_right = font_score.render(f"STATUS: {status_txt}", True, status_color)
        screen.blit(s_left, (10, top_y1))
        screen.blit(s_right, (screen.get_width() - s_right.get_width() - 10, top_y1))

        # Dòng 2 & Dòng 3: Steps, Cost, Nodes Expanded, Execution Time, Lộ trình Path
        if search_stats:
            steps = len(search_stats["actions"]) if search_stats.get("actions") else 0
            cost = search_stats.get("total_cost", 0)
            nodes = search_stats.get("nodes_expanded", 0)
            time_ms = search_stats.get("execution_time", 0) * 1000
            info_str = f"Steps: {steps}  |  Cost: {cost}  |  Nodes: {nodes}  |  Time: {time_ms:.2f}ms"
            
            actions = search_stats.get("actions") or []
            if actions:
                path_str = " -> ".join(actions)
                if len(path_str) > 65:
                    path_str = path_str[:62] + "..."
                path_display = f"Path: {path_str}"
            else:
                path_display = "Path: None"
        else:
            info_str = "Calculating path..."
            path_display = ""

        s_info = font_small.render(info_str, True, COLORS['W'])
        screen.blit(s_info, (10, top_y2))

        # Dòng 3: Trạng thái animation + hướng dẫn phím
        search_phase = getattr(game_obj, 'search_phase', None) if game_obj else None
        if search_phase == "EXPLORING":
            explored_n = len(getattr(game_obj, 'explored_cells', set()))
            total_n = len(getattr(game_obj, 'explore_trace', []))
            is_paused = getattr(game_obj, 'paused', True)
            phase_hint = f"Đang quét: {explored_n}/{total_n} node  |  {'[SPACE] Chạy  [S] Step' if is_paused else '[SPACE] Tạm dừng'}"
            hint_color = (255, 200, 80) if is_paused else (100, 220, 120)
        elif search_phase == "PATH_FOUND":
            phase_hint = "✓ Tìm ra đường! Nhấn [SPACE] hoặc [S] để Pacman bắt đầu đi"
            hint_color = (100, 255, 100)
        elif search_phase == "WALKING":
            is_paused = getattr(game_obj, 'paused', False)
            phase_hint = f"Pacman đang đi theo đường...  |  {'[SPACE] Tiếp  [S] Step' if is_paused else '[SPACE] Tạm dừng'}"
            hint_color = (255, 215, 0)
        elif search_phase == "NO_PATH":
            phase_hint = "✗ Không tìm thấy đường đến mồi!"
            hint_color = (231, 76, 60)
        else:
            phase_hint = ""
            hint_color = COLORS['W']

        if phase_hint:
            s_phase = font_small.render(phase_hint, True, hint_color)
            screen.blit(s_phase, (10, top_y3))

    # 2. Chế độ 2: Đối kháng AI vs AI
    elif mode == 2:
        # Dòng 1: Chế độ + Điểm số Score
        s_left = font_big.render(f"{mode_text} ({map_text})", True, COLORS['Y'])
        s_score = font_score.render(f"SCORE: {score}", True, COLORS['Y'])
        screen.blit(s_left, (10, top_y1))
        screen.blit(s_score, (screen.get_width() - s_score.get_width() - 10, top_y1))

        # Dòng 2: Tác tử, Độ sâu, Nodes xét, Thời gian ra quyết định
        # Dòng 3: Nước đi đã chọn, Giá trị đánh giá Heuristic
        if agent_stats:
            agent_name = agent_stats.get("agent", "AlphaBeta")
            depth = agent_stats.get("depth", 1)
            nodes = agent_stats.get("nodes", 0)
            time_ms = agent_stats.get("time_ms", 0.0)
            action = agent_stats.get("action", "NONE")
            val = agent_stats.get("value", 0.0)

            line2 = f"Agent: {agent_name} (Depth: {depth})  |  Nodes: {nodes}  |  Time: {time_ms:.2f}ms"
            line3 = f"Decision: Action = {action}  |  Evaluation Value = {val:.2f}"
        else:
            line2 = "Waiting for decision..."
            line3 = ""

        s_info = font_small.render(line2, True, COLORS['W'])
        screen.blit(s_info, (10, top_y2))


    # 3. Chế độ 1: Người chơi vs Ma AI
    else:
        s1 = font_big.render(f"{mode_text} ({map_text})", True, COLORS['Y'])
        s_score = font_score.render(f"SCORE: {score}", True, COLORS['Y'])
        screen.blit(s1, (10, top_y1))
        screen.blit(s_score, (screen.get_width() - s_score.get_width() - 10, top_y1))

        s2 = font_small.render("Dieu khien Pacman bang 4 phim mui ten | Tranh cac con ma AI", True, COLORS['W'])
        s3 = font_small.render("Phim SPACE: Pause  |  S: Di 1 buoc  |  R: Choi lai", True, (180, 180, 180))
        screen.blit(s2, (10, top_y2))
        screen.blit(s3, (10, top_y3))

def draw_box_search_result(screen, game, screen_width, screen_height):
    """Hộp thông báo kết quả tìm kiếm với đầy đủ các thông số theo yêu cầu đề bài."""
    stats = game.search_stats or {}
    total_cost = stats.get("total_cost", 0)
    nodes = stats.get("nodes_expanded", 0)
    exec_time_ms = stats.get("execution_time", 0.0) * 1000
    goal_mode_str = "Ăn 1 mồi (Single Goal)" if getattr(game, 'goal_type', 'single') == "single" else "Ăn nhiều mồi (Multi-Food)"
    algo_str = (game.algo_name or "A*").upper()

    box_width = min(420, screen_width - 20)
    box_height = 220
    box_x = (screen_width - box_width) // 2
    box_y = (screen_height - box_height) // 2
    box_rect = pygame.Rect(box_x, box_y, box_width, box_height)

    pygame.draw.rect(screen, COLORS.get('BG', (3, 3, 3)), box_rect, border_radius=12)
    border_color = (46, 204, 113) if game.status == "WIN" else (231, 76, 60)
    pygame.draw.rect(screen, border_color, box_rect, 3, border_radius=12)

    if game.status == "WIN":
        title_surf = game.font_bigger.render("VICTORY!", True, COLORS['Y'])
        status_sub = "ĐÃ TÌM THẤY VÀ ĂN HẾT MỤC TIÊU"
    else:
        title_surf = game.font_bigger.render("NO SOLUTION", True, (231, 76, 60))
        status_sub = "KHÔNG TÌM THẤY ĐƯỜNG ĐẾN MỒI!"

    screen.blit(title_surf, title_surf.get_rect(center=(box_rect.centerx, box_y + 30)))

    sub_surf = game.font_small.render(status_sub, True, COLORS['W'])
    screen.blit(sub_surf, sub_surf.get_rect(center=(box_rect.centerx, box_y + 65)))

    line1 = f"Chế độ: {goal_mode_str}"
    line2 = f"Thuật toán: {algo_str}  |  Chi phí: {total_cost} bước"
    line3 = f"Nodes duyệt: {nodes}  |  Thời gian: {exec_time_ms:.2f} ms"
    line4 = f"Điểm số: {game.score}  |  [R] Chơi lại  |  [ESC] Menu"

    for idx, (txt, color) in enumerate([
        (line1, COLORS['W']),
        (line2, (72, 227, 253)),
        (line3, (72, 227, 253)),
        (line4, COLORS['Y'])
    ]):
        surf = game.font_small.render(txt, True, color)
        screen.blit(surf, surf.get_rect(center=(box_rect.centerx, box_y + 100 + idx * 26)))


def draw_box_winlose(screen, title_text, sub_text, font_title, font_sub, screen_width, screen_height):
    GAP = 20
    PAD = 60
    box_width = 360

    '''box_width = 360
    box_height = 180
    box_x = (screen_width - box_width) // 2
    box_y = (screen_height - box_height) // 2
    box_rect = pygame.Rect(box_x, box_y, box_width, box_height)'''

    title_surf = font_title.render(title_text, True, COLORS.get('Y', (255, 245, 59)))
    sub_surf = font_sub.render(sub_text, True, COLORS.get('Y', (255, 245, 59)))

    t_ink = title_surf.get_bounding_rect()
    s_ink = sub_surf.get_bounding_rect()

    box_height = PAD + t_ink.height + GAP + s_ink.height + PAD
    box_x = (screen_width - box_width) // 2
    box_y = (screen_height - box_height) // 2
    box_rect = pygame.Rect(box_x, box_y, box_width, box_height)

    pygame.draw.rect(screen, COLORS.get('BG', (3, 3, 3)), box_rect, border_radius=12)
    pygame.draw.rect(screen, COLORS.get('BL'), box_rect, 3, border_radius=12)

    title_y = box_rect.y + PAD - t_ink.top
    sub_y = box_rect.y + PAD + t_ink.height + GAP - s_ink.top
    screen.blit(title_surf, title_surf.get_rect(midtop=(box_rect.centerx, title_y)))
    screen.blit(sub_surf, sub_surf.get_rect(midtop=(box_rect.centerx, sub_y)))


def draw_game_screen(screen, game):
    """Gom toàn bộ việc vẽ màn hình game vào một nơi duy nhất."""
    screen.fill(COLORS['BG'])
    draw_map(screen, game.map_data, game.wall_surf)

    # Vẽ ô đã khám phá (xanh nhạt) và đường đi (vàng) cho Mode 3
    if game.mode == 3:
        EXPLORED_COLOR = (80, 160, 255)    # xanh nhạt
        EXPLORED_BORDER = (60, 120, 200)
        PATH_COLOR     = (255, 215, 0)     # vàng
        PATH_BORDER    = (200, 160, 0)

        for (cx, cy) in getattr(game, 'explored_cells', set()):
            rect = pygame.Rect(cx * SIZE, cy * SIZE + LE_TREN, SIZE, SIZE)
            pygame.draw.rect(screen, EXPLORED_COLOR, rect)
            pygame.draw.rect(screen, EXPLORED_BORDER, rect, 1)

        phase = getattr(game, 'search_phase', None)
        if phase in ("PATH_FOUND", "WALKING"):
            for (cx, cy) in getattr(game, 'path_cells', []):
                rect = pygame.Rect(cx * SIZE, cy * SIZE + LE_TREN, SIZE, SIZE)
                pygame.draw.rect(screen, PATH_COLOR, rect)
                pygame.draw.rect(screen, PATH_BORDER, rect, 1)


    # 1. Vẽ các con Ma (Chế độ 3 không có ma)
    if game.mode != 3:
        now = pygame.time.get_ticks()
        for i, pos in enumerate(game.ghost_pos):
            draw_g(screen, pos, game.ghost_art(i, now))

    # 2. Vẽ Pacman
    show_pacman = True
    if game.status == "DYING":
        elapsed = pygame.time.get_ticks() - game.dying_start
        show_pacman = (elapsed // BLINK_MS) % 2 == 1
    if show_pacman:
        draw_p(screen, game.pacman_pos, game.pacman_dir)

    # 3. Vẽ thanh thông số HUD (Mục 4)
    agent_stats = game.pacman_agent.last_stats if game.pacman_agent else None
    draw_hud(screen, game.map_data, game.mode, game.mode_text, game.map_text, game.score,
             game.font_big, game.font_small, game.font_score,
             search_stats=game.search_stats, algo_name=game.algo_name, agent_stats=agent_stats,
             game_obj=game)

    # =========================================================
    # VẼ 3 NÚT ĐIỀU KHIỂN CÁCH ĐỀU NHAU Ở DƯỚI BẢN ĐỒ
    # =========================================================
    screen_w = screen.get_width()
    map_bottom = LE_TREN + game.map_data.rows * SIZE
    
    btn_w = 140   # Chiều rộng mỗi nút
    btn_h = 28    # Chiều cao mỗi nút
    btn_y = map_bottom + (LE_DUOI - btn_h) // 2  # Căn giữa theo chiều dọc dải dưới
    
    # Tính khoảng cách cách đều 4 phía
    gap = (screen_w - 3 * btn_w) // 4

    # 1. NÚT 1: PAUSE / RESUME [SPACE]
    x1 = gap
    btn_pause_rect = pygame.Rect(x1, btn_y, btn_w, btn_h)
    pause_text = "RESUME [Space]" if game.paused else "PAUSE [Space]"
    pause_color = (230, 120, 30) if game.paused else (50, 50, 60) # Cam khi dừng, Xám khi chạy
    pygame.draw.rect(screen, pause_color, btn_pause_rect, border_radius=6)
    pygame.draw.rect(screen, COLORS['W'], btn_pause_rect, width=1, border_radius=6) # Viền trắng
    txt_pause = game.font_small.render(pause_text, True, COLORS['W'])
    screen.blit(txt_pause, txt_pause.get_rect(center=btn_pause_rect.center))

    # 2. NÚT 2: STEP [S]
    x2 = gap * 2 + btn_w
    btn_step_rect = pygame.Rect(x2, btn_y, btn_w, btn_h)
    step_color = (40, 100, 200) if game.paused else (40, 40, 45) # Xanh sáng khi pause, xám mờ khi đang chạy
    pygame.draw.rect(screen, step_color, btn_step_rect, border_radius=6)
    pygame.draw.rect(screen, COLORS['W'] if game.paused else (100, 100, 100), btn_step_rect, width=1, border_radius=6)
    txt_step = game.font_small.render("STEP [S]", True, COLORS['W'] if game.paused else (150, 150, 150))
    screen.blit(txt_step, txt_step.get_rect(center=btn_step_rect.center))

    # 3. NÚT 3: RESTART [R]
    x3 = gap * 3 + btn_w * 2
    btn_restart_rect = pygame.Rect(x3, btn_y, btn_w, btn_h)
    pygame.draw.rect(screen, (180, 45, 45), btn_restart_rect, border_radius=6) # Đỏ
    pygame.draw.rect(screen, COLORS['W'], btn_restart_rect, width=1, border_radius=6)
    txt_restart = game.font_small.render("RESTART [R]", True, COLORS['W'])
    screen.blit(txt_restart, txt_restart.get_rect(center=btn_restart_rect.center))


    # 5. Vẽ hộp thông báo Thắng / Thua / Không có đường đi
    w, h = screen.get_width(), screen.get_height()
    if game.mode == 3:
        if game.status in ("WIN", "NO_PATH"):
            draw_box_search_result(screen, game, w, h)
    else:
        if game.status == "LOSE":
            draw_box_winlose(screen, "YOU LOSE", "DIU CAN ĐU ỊT", game.font_bigger, game.font_score, w, h)
        elif game.status == "WIN":
            draw_box_winlose(screen, "YOU WIN", "THẮNG GÒI ĐÓ, VUI HĂM", game.font_bigger, game.font_score, w, h)

    # Trả về tọa độ 3 nút để game_screen bắt click
    return btn_pause_rect, btn_step_rect, btn_restart_rect