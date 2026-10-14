import random

MAP_SIZES = {
    1: (21, 11),  # Tiny Maze (Nhỏ)
    2: (27, 15),  # Medium Maze (Vừa)
    3: (33, 19),  # Big Maze (Lớn)
}

GHOST_HOUSE = [
    "%%%-%%%",
    "%     %",
    "%G G G%",
    "%%%%%%%",
]


def neighbors4(r, c):
    """4 ô kề (trên, dưới, trái, phải) của ô hàng r, cột c."""
    return [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]


def is_walkable(grid, r, c):
    """Ô này Pacman có thể đứng không? (nằm trong map, không phải tường, không phải cửa nhà ma)"""
    return 0 <= r < len(grid) and 0 <= c < len(grid[0]) and grid[r][c] not in ('%', '-')


def carve_maze(grid):
    """Đào đường đi bằng DFS: bắt đầu ở (1,1), đi ngẫu nhiên, hết đường thì lùi lại."""
    height, width = len(grid), len(grid[0])
    grid[1][1] = ' '
    stack = [(1, 1)]
    while stack:
        r, c = stack[-1]
        options = []
        for dr, dc in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            nr, nc = r + dr, c + dc
            if 0 < nr < height - 1 and 0 < nc < width - 1 and grid[nr][nc] == '%':
                options.append((nr, nc, r + dr // 2, c + dc // 2))
        if options:
            nr, nc, wr, wc = random.choice(options)
            grid[wr][wc] = ' '
            grid[nr][nc] = ' '
            stack.append((nr, nc))
        else:
            stack.pop()


def add_loops(grid, chance, protected):
    """Với mỗi bức tường nằm GIỮA 2 đoạn đường, có xác suất `chance` bị đập để tạo đường vòng.
    Chỉ đập tường có đường ở 2 phía đối diện nên không bao giờ tạo ra ô bị cô lập."""
    height, width = len(grid), len(grid[0])
    for r in range(1, height - 1):
        for c in range(1, width - 1):
            if grid[r][c] != '%' or (r, c) in protected:
                continue
            ngang = is_walkable(grid, r, c - 1) and is_walkable(grid, r, c + 1)
            doc = is_walkable(grid, r - 1, c) and is_walkable(grid, r + 1, c)
            if (ngang or doc) and random.random() < chance:
                grid[r][c] = ' '


def place_ghost_house(grid):
    """Đặt nhà ma ở giữa map, chừa 1 vòng đường quanh nhà. Trả về tập các ô cần được bảo vệ."""
    height, width = len(grid), len(grid[0])
    h, w = len(GHOST_HOUSE), len(GHOST_HOUSE[0])
    top, left = height // 2 - h // 2, width // 2 - w // 2
    protected = set()

    for r in range(top - 1, top + h + 1):
        for c in range(left - 1, left + w + 1):
            if 1 <= r <= height - 2 and 1 <= c <= width - 2:
                grid[r][c] = ' '
                protected.add((r, c))

    for i, line in enumerate(GHOST_HOUSE):
        for j, ch in enumerate(line):
            grid[top + i][left + j] = ch
    return protected


def wall_off_islands(grid):
    """Giữ lại vùng đi được LỚN NHẤT; vùng nào bị tách rời thì lấp thành tường."""
    height, width = len(grid), len(grid[0])
    seen = set()
    regions = []
    for r in range(height):
        for c in range(width):
            if (r, c) in seen or grid[r][c] == '%':
                continue
            region, stack = [], [(r, c)]
            seen.add((r, c))
            while stack:
                cr, cc = stack.pop()
                region.append((cr, cc))
                for nr, nc in neighbors4(cr, cc):
                    if 0 <= nr < height and 0 <= nc < width \
                            and grid[nr][nc] != '%' and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            regions.append(region)

    biggest = max(regions, key=len)
    for region in regions:
        if region is not biggest:
            for r, c in region:
                grid[r][c] = '%'


def remove_dead_ends(grid, protected):
    """Ngõ cụt = ô đi được mà chỉ có 1 ô đi được kề bên. Phá 1 bức tường để nối nó sang đường khác."""
    height, width = len(grid), len(grid[0])
    for _ in range(10):
        changed = False
        for r in range(1, height - 1):
            for c in range(1, width - 1):
                if grid[r][c] != ' ' or (r, c) in protected:
                    continue
                if sum(is_walkable(grid, nr, nc) for nr, nc in neighbors4(r, c)) > 1:
                    continue
                options = []
                for wr, wc in neighbors4(r, c):
                    fr, fc = 2 * wr - r, 2 * wc - c
                    if grid[wr][wc] == '%' and (wr, wc) not in protected \
                            and 1 <= wr <= height - 2 and 1 <= wc <= width - 2 \
                            and is_walkable(grid, fr, fc):
                        options.append((wr, wc))
                if options:
                    wr, wc = random.choice(options)
                    grid[wr][wc] = ' '
                    changed = True
        if not changed:
            return


def fill_goals(grid):
    """Mọi ô trống thành goal2 ('.'), 4 góc là goal1 ('o')."""
    height, width = len(grid), len(grid[0])
    for r in range(height):
        for c in range(width):
            if grid[r][c] == ' ':
                grid[r][c] = '.'
    for tr, tc in [(1, 1), (1, width - 2), (height - 2, 1), (height - 2, width - 2)]:
        best, best_d = None, 10 ** 9
        for r in range(height):
            for c in range(width):
                if grid[r][c] == '.' and abs(r - tr) + abs(c - tc) < best_d:
                    best, best_d = (r, c), abs(r - tr) + abs(c - tc)
        if best:
            grid[best[0]][best[1]] = 'o'


def place_pacman(grid):
    """Đặt 'P' ở ô goal gần giữa hàng dưới cùng nhất."""
    height, width = len(grid), len(grid[0])
    best, best_d = None, 10 ** 9
    for r in range(height):
        for c in range(width):
            if grid[r][c] == '.':
                d = abs(r - (height - 2)) * 2 + abs(c - width // 2)
                if d < best_d:
                    best, best_d = (r, c), d
    grid[best[0]][best[1]] = 'P'


def gen_map(map_type=1, with_ghost=False, seed=None):
    """
    map_type  : 1 = Tiny, 2 = Medium, 3 = Big (kích thước lấy từ MAP_SIZES)
    with_ghost: False = map không ma (được có ngõ cụt)
                True  = map có nhà ma ở giữa, ít ngõ cụt, nhiều lối đi vòng
    seed      : cùng số thì ra cùng map (để debug); None thì mỗi lần một map khác
    Trả về list các chuỗi, mỗi chuỗi là 1 hàng của map.
    """
    if seed is not None:
        random.seed(seed)

    width, height = MAP_SIZES[map_type]
    grid = [['%' for _ in range(width)] for _ in range(height)]

    carve_maze(grid)

    if with_ghost:
        protected = place_ghost_house(grid)
        wall_off_islands(grid)
        add_loops(grid, 0.12, protected)
        remove_dead_ends(grid, protected)
        wall_off_islands(grid)
    else:
        add_loops(grid, 0.08, set())

    fill_goals(grid)

    if with_ghost:
        h, w = len(GHOST_HOUSE), len(GHOST_HOUSE[0])
        top, left = height // 2 - h // 2, width // 2 - w // 2
        for i in range(1, h - 1):
            for j in range(1, w - 1):
                if grid[top + i][left + j] in ('.', 'o'):
                    grid[top + i][left + j] = ' '

    place_pacman(grid)
    return ["".join(row) for row in grid]


if __name__ == "__main__":
    for ghost in (False, True):
        print("Có ma" if ghost else "Không ma")
        print("\n".join(gen_map(1, ghost)))
        print()