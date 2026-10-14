#=========================================
#Bảng quy ước ký hiệu bản đồ
#=========================================

WALL_CHAR = '%'     #ký tự tường,điền vào trong ngoặc nhá
FOOD_CHAR = '.'     #đồ ănggggggg
PACMAN_CHAR = 'P'   #con pacman
GHOST_CHAR = 'G'    #con ma
CAPSULE_CHAR = 'o'  #cái hạt năng lượng to ăn vào được cộng nhiều điểm hơn hạt food í
EMPTY_CHAR = ' '    #trống không

class Layout:
    """lưu thông tin bản đồ sau khi đọc từ file maps.txt"""
    def __init__(self):
        self.pacman_start = None # Tọa độ x y của pacman
        self.ghost_starts = []   # Danh sách tọa độ x y của các con ma
        self.food = []           # Grid 2D chứa Bool (True là có mồi)
        self.walls = []          # Grid 2D chứa Bool (True là tường)
        self.capsules = []       # List [(x1, y1),(x2,y2)...] tọa độ các viên năng lượng to
        self.height = 0          # số hàng của bản đồ y
        self.width = 0           # số cột của bản đồ x
        self.wall_types = []      # Grid 2D chứa loại tường (dạng string) cho từng ô tường

def load_map(file_path):
#Đọc file map .txt và lưu thông tin vào đối tượng Layout.
# 1. Mở và đọc toàn bộ các dòng trong file .txt
    with open(file_path, 'r') as f:
        lines = [line.strip('\r\n') for line in f.readlines() if line.strip('\r\n')]

    layout = Layout()
    layout.height = len(lines)
    layout.width = len(lines[0]) if layout.height > 0 else 0

    # 2. Khởi tạo sẵn ma trận 2D toàn giá trị False cho walls và food
    layout.walls = [[False for _ in range(layout.width)] for _ in range(layout.height)]
    layout.food = [[False for _ in range(layout.width)] for _ in range(layout.height)]

    # 3. Duyệt qua từng ô (y: hàng, x: cột) trong file text
    for y in range(layout.height):
        for x in range(layout.width):
            char = lines[y][x]

            if char == WALL_CHAR:
                layout.walls[y][x] = True
            elif char == FOOD_CHAR:
                layout.food[y][x] = True
            elif char == PACMAN_CHAR:
                layout.pacman_start = (x, y)
            elif char == GHOST_CHAR:
                layout.ghost_starts.append((x, y))
            elif char == CAPSULE_CHAR:
                layout.capsules.append((x, y))

    # 4. Giá trị an toàn mặc định nếu map quên đặt Pacman
    if layout.pacman_start is None:
        layout.pacman_start = (1, 1)
    #tạo 1 ma trận có cùng kích thước 
    layout.wall_types = [[None for _ in range(layout.width)] for _ in range(layout.height)]
    #gán tường vào từng ô
    for y in range(layout.height):
        for x in range(layout.width):
            if layout.walls[y][x]:
                layout.wall_types[y][x] = calculate_wall_type(layout.walls, x, y, layout.height, layout.width)
    return layout


def calculate_wall_type(walls, x, y, height, width):
    """Xác định loại tường dựa trên các ô xung quanh."""
    has_north = (y > 0) and walls[y - 1][x]
    has_south = (y < height - 1) and walls[y + 1][x]
    has_west = (x > 0) and walls[y][x - 1]
    has_east = (x < width - 1) and walls[y][x + 1]

    # Kiểm tra các góc tường
    if has_south and not has_north and not has_west and has_east:
        return "corner_top_left"
    elif has_south and has_west and not has_north and not has_east:
        return "corner_top_right"
    elif has_north and has_east and not has_south and not has_west:
        return "corner_bottom_left"
    elif has_north and has_west and not has_south and not has_east:
        return "corner_bottom_right"

    # Kiểm tra các cạnh tường
    if has_north and has_south and not has_west and not has_east:
        return "vertical"
    elif has_west and has_east and not has_north and not has_south:
        return "horizontal"

    # Các ngã ba, ngã 4 hoặc ngõ cụt
    return "wall_default"