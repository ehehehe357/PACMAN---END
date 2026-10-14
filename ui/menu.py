import os
import pygame
import sys
from ui.pixel_assets import COLORS

b_width = 400
b_height = 50

FONT_HEADING = "04B_30__.TTF"
FONT_MAIN = "SVN-Determination Sans.otf"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_font(filename, size):
    for folder in ("assets/fonts", "assets"):
        path = os.path.join(BASE_DIR, folder, filename)
        if os.path.isfile(path):
            return pygame.font.Font(path, size)
    return pygame.font.SysFont("arial", size, bold=True)

class Menu:
    def __init__(self, screen, width, height):
        self.screen = screen
        self.width = width
        self.height = height
        self.title_heading_1 = load_font(FONT_HEADING, 56)
        self.font_title = load_font(FONT_MAIN, 48)
        self.font_button = load_font(FONT_MAIN, 24)
        self.font_button_small = load_font(FONT_MAIN, 20)
        self.font_sub = load_font(FONT_MAIN, 16)

        self.current_state = 1
        self.selected_mode = None
        self.selected_map = None
        self.selected_algo = None
        self.selected_goal_type = "single"  # "single" hoặc "multi"

        self.option1 = [
            "Start",
            "Exit"
        ]
        self.option2 = [
            "Player vs AI Ghosts\nNgười chơi vs Ma AI", 
            "AI vs AI Autoplay\nPacman AI vs Ma AI", 
            "Discovery Mode\nTìm kiếm đường đi", 
            "Back"
        ]
        # Option 5: Chọn kiểu tìm kiếm cho Mode 3
        self.option_goal_type = [
            "Single Goal Search\nTìm đường ăn 1 mồi",
            "Multi-Food Search\nTìm đường ăn nhiều mồi",
            "Back"
        ]
        # Map cho Mode 1, 2
        self.option3_standard = [
            "Tiny Maze", 
            "Medium Maze", 
            "Big Maze",
            "Back"
        ]
        # Map cho Mode 3: có thêm Map cụt (Unreachable Maze)
        self.option3_discovery = [
            "Tiny Maze", 
            "Medium Maze", 
            "Big Maze",
            "Unreachable Maze\nMap cụt (Không có đường)",
            "Back"
        ]
        self.option4 = [
            "A* Search",
            "Breadth-First Search (BFS)",
            "Uniform-Cost Search (UCS)",
            "Greedy Best-First Search",
            "Depth-First Search (DFS)",
            "Back"
        ]
        self.selected_index = 0

    @property
    def option3(self):
        if self.selected_mode == 3:
            return self.option3_discovery
        return self.option3_standard

    def reset(self):
        self.current_state = 1
        self.selected_index = 0
        self.selected_mode = None
        self.selected_map = None
        self.selected_algo = None
        self.selected_goal_type = "single"
    
    def get_current_options(self):
        if self.current_state == 1:
            return self.option1
        elif self.current_state == 2:
            return self.option2
        elif self.current_state == 3:
            return self.option3
        elif self.current_state == 4:
            return self.option4
        elif self.current_state == 5:
            return self.option_goal_type
        return self.option1

    def draw_box(self, options, start_y, gap_y=70):
        for i, text in enumerate(options):
            is_selected = (i == self.selected_index)
            text_color = COLORS.get('W') if is_selected else COLORS.get('Y')

            box_x = (self.width - b_width) // 2
            box_y = start_y + i * gap_y
            box_rect = pygame.Rect(box_x, box_y, b_width, b_height)

            box_bg_color = COLORS.get('BG') if not is_selected else COLORS.get("BL")

            pygame.draw.rect(self.screen, box_bg_color, box_rect, border_radius=8)
            pygame.draw.rect(self.screen, COLORS.get('BL'), box_rect, 2, border_radius=8)

            lines = text.split("\n")

            if len(lines) == 1:
                surf = self.font_button.render(lines[0], True, text_color)
                self.screen.blit(surf, surf.get_rect(center=box_rect.center))
            else:
                s1 = self.font_button.render(lines[0], True, text_color)
                s2 = self.font_sub.render(lines[1], True, text_color)
                self.screen.blit(s1, s1.get_rect(center=(box_rect.centerx, box_rect.y + 15)))
                self.screen.blit(s2, s2.get_rect(center=(box_rect.centerx, box_rect.y + 36)))

    def get_box_rects(self):
        options = self.get_current_options()
        if self.current_state == 1:
            start_y, gap_y = 280, 70
        elif self.current_state == 4:
            start_y, gap_y = 110, 55
        elif self.current_state == 3 and self.selected_mode == 3:
            start_y, gap_y = 130, 60
        else:
            start_y, gap_y = 150, 70

        rects = []
        for i in range(len(options)):
            x = (self.width - b_width) // 2
            rects.append(pygame.Rect(x, start_y + i * gap_y, b_width, b_height))
        return rects

    def draw(self):
        bg_color = COLORS.get('BG')
        self.screen.fill(bg_color)
        heading_color = COLORS.get('Y')

        if self.current_state == 1:
            title_surf = self.title_heading_1.render("PACMAN", True, heading_color)
            title_rect = title_surf.get_rect(center=(self.width // 2, 150))
            self.screen.blit(title_surf, title_rect)
            self.draw_box(self.option1, start_y=280)

        elif self.current_state == 2:
            title_surf = self.font_title.render("CHỌN CHẾ ĐỘ", True, heading_color)
            title_rect = title_surf.get_rect(center=(self.width // 2, 90))
            self.screen.blit(title_surf, title_rect)
            self.draw_box(self.option2, start_y=140)

        elif self.current_state == 5:
            title_surf = self.font_title.render("MỤC TIÊU TÌM KIẾM", True, heading_color)
            title_rect = title_surf.get_rect(center=(self.width // 2, 90))
            self.screen.blit(title_surf, title_rect)
            self.draw_box(self.option_goal_type, start_y=160)

        elif self.current_state == 3:
            title_surf = self.font_title.render("CHỌN BẢN ĐỒ", True, heading_color)
            title_rect = title_surf.get_rect(center=(self.width // 2, 80))
            self.screen.blit(title_surf, title_rect)
            gap_y = 60 if self.selected_mode == 3 else 70
            start_y = 130 if self.selected_mode == 3 else 150
            self.draw_box(self.option3, start_y=start_y, gap_y=gap_y)

        elif self.current_state == 4:
            title_surf = self.font_title.render("CHỌN THUẬT TOÁN", True, heading_color)
            title_rect = title_surf.get_rect(center=(self.width // 2, 50))
            self.screen.blit(title_surf, title_rect)
            self.draw_box(self.option4, start_y=110, gap_y=55)

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            current_options = self.get_current_options()

            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(current_options)
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(current_options)
            elif event.key == pygame.K_RETURN:
                # --- GIAO DIỆN 1: START / EXIT ---
                if self.current_state == 1:
                    if self.selected_index == 0:
                        self.current_state = 2
                        self.selected_index = 0
                    elif self.selected_index == 1:
                        return "EXIT"

                # --- GIAO DIỆN 2: CHỌN CHẾ ĐỘ ---
                elif self.current_state == 2:
                    if self.selected_index == 3:  # Nút Quay lại
                        self.current_state = 1
                        self.selected_index = 0
                    elif self.selected_index == 2:  # Discovery Mode
                        self.selected_mode = 3
                        self.current_state = 5  # Chuyển qua chọn kiểu mồi
                        self.selected_index = 0
                    else:  # Mode 1 (Người chơi) hoặc Mode 2 (AI vs AI)
                        self.selected_mode = self.selected_index + 1
                        self.current_state = 3  # Chuyển qua chọn Map
                        self.selected_index = 0

                # --- GIAO DIỆN 5: CHỌN MỤC TIÊU TÌM KIẾM (Ăn 1 mồi / Ăn nhiều mồi) ---
                elif self.current_state == 5:
                    if self.selected_index == 2:  # Nút Quay lại
                        self.current_state = 2
                        self.selected_index = 2
                    else:
                        self.selected_goal_type = "single" if self.selected_index == 0 else "multi"
                        self.current_state = 3  # Chuyển qua chọn Map
                        self.selected_index = 0

                # --- GIAO DIỆN 3: CHỌN MAP ---
                elif self.current_state == 3:
                    back_idx = len(self.option3) - 1
                    if self.selected_index == back_idx:
                        # Quay lại
                        if self.selected_mode == 3:
                            self.current_state = 5
                            self.selected_index = 0 if self.selected_goal_type == "single" else 1
                        else:
                            self.current_state = 2
                            self.selected_index = self.selected_mode - 1
                    else:
                        self.selected_map = self.selected_index + 1
                        if self.selected_mode == 3:
                            self.current_state = 4  # Chuyển qua chọn thuật toán
                            self.selected_index = 0
                        else:
                            return {
                                "action": "START_GAME",
                                "mode": self.selected_mode,
                                "map": self.selected_map,
                                "goal_type": "single"
                            }

                # --- GIAO DIỆN 4: CHỌN THUẬT TOÁN ---
                elif self.current_state == 4:
                    if self.selected_index == 5:  # Nút Quay lại
                        self.current_state = 3
                        self.selected_index = 0
                    else:
                        algo_map = {
                            0: "astar",
                            1: "bfs",
                            2: "ucs",
                            3: "greedy",
                            4: "dfs"
                        }
                        self.selected_algo = algo_map[self.selected_index]
                        return {
                            "action": "START_GAME",
                            "mode": self.selected_mode,
                            "map": self.selected_map,
                            "algo": self.selected_algo,
                            "goal_type": self.selected_goal_type
                        }

        elif event.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(self.get_box_rects()):
                if rect.collidepoint(event.pos):
                    self.selected_index = i

        elif event.type == pygame.MOUSEBUTTONDOWN:
            for i, rect in enumerate(self.get_box_rects()):
                if rect.collidepoint(event.pos):
                    self.selected_index = i
                    return self.handle_input(
                        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
                    )

        return None