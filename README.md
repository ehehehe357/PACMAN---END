# PACMAN
## Nhóm 15

### I. DANH SÁCH THÀNH VIÊN
| MSSV | Họ và tên | Phần phụ trách |
| --- | --- | --- |
| 25022800 | Lê Quỳnh Chi | THêy |
| 25022986 | Nguyễn Lê Mai Phương | Giao diện (UI), bản đồ (maps) |
| 25022956 | Thăng Đại Nam | Heey hêy |
| 25022998 | Nguyễn Mạnh Quân | Hey hey hey |

### II. Phiên bản Python và hệ điều hành
| Thành phần | Phiên bản
| --- | --- |
| Python | 3.13.7 |
| Pygame | 2.6.1 |
| Hệ điều hành | Win 11 |

### III. Cách cài đặt
1. Cài python (phiên bản ở mục II)
2. 
3. (Khuyến nghị) Tạo môi trường ảo để không lẫn với các môi trường khác
```bash
    python -m venv venv
    venv\Scripts\activate
```
4. Cài thư viện
```bash
    pip install -r requirements.txt
```

### IV. Cấu trúc chương trình
```
.
├── main.py                  # Điểm khởi chạy: tạo cửa sổ, chuyển giữa menu và màn hình chơi
├── requirements.txt         # Danh sách thư viện cần cài
├── README.md
├── README_multiagents.md    # Tài liệu chi tiết phần tìm kiếm đối kháng
├── CONTRIBUTIONS.md         
├── assets/                  # Font chữ
├── ui/                      # Giao diện (pygame)
│   ├── menu.py              #   Menu chọn chế độ và bản đồ
│   ├── game_screen.py       #   Màn hình chơi: vòng lặp game, xử lý phím, ăn mồi, ma, thắng/thua
│   ├── display.py           #   Các hàm vẽ: tường, mồi, Pacman, ma, thanh điểm
│   └── pixel_assets.py      #   Màu sắc và hình pixel của nhân vật
├── maps/                    # Bản đồ
│   ├── gen_map.py           #   Sinh bản đồ ngẫu nhiên
│   ├── map_generator.py     #   Đọc bản đồ, chọn cách lấy bản đồ (sinh hay đọc file)
│   └── *.txt                #   Các bản đồ cố định (tinyMaze, costMaze, adv_*, ...)
├── src/                     # Logic và thuật toán
│   ├── engine.py            #   GameState: trạng thái ván chơi và luật chơi
│   ├── search.py            #   DFS, BFS, UCS, Greedy, A*
│   ├── searchAgents.py      #   Bài toán tìm đường, heuristic, SearchAgent
│   ├── multiAgents.py       #   Minimax, Alpha-Beta, Expectimax, ma mô phỏng
│   ├── evaluation.py        #   Các hàm đánh giá trạng thái
│   ├── map_loader.py        #   Đọc file bản đồ thành Layout cho engine
│   └── util.py              #   Stack, Queue, PriorityQueue
├── tests/                   # Kiểm thử và thực nghiệm
│   ├── test_search.py       #   Test các thuật toán tìm đường
│   ├── test_multiagent.py   #   Test phần đối kháng
│   ├── helpers.py           #   Hàm dùng chung cho test
│   ├── benchmark.py         #   Thực nghiệm so sánh thuật toán tìm đường
│   └── benchmark_multiagent.py  # Thực nghiệm Minimax vs Alpha-Beta
└── results/                 # Kết quả thực nghiệm (CSV, biểu đồ)
```

### V. Cách khởi động và sử dụng giao diện
**5.1. Khởi động**
Lệnh chạy từ thư mục gốc
```bash
    python main.py
```
**5.2. Menu**
- Trong giao diện Menu, ấn mũi tên lên xuống để chọn, Enter để xác nhận, hoặc có thể dùng chuột, ấn Back để quay trở lại màn hình trước.
- Luồng:
```
    Màn hình chính (Start / Exit)
    ├── Chọn chế độ 
        ├── 1. Player vs AI Ghosts (Người chơi với ma AI) 
        |   ├── Chọn map (Tiny, Medium, Big)
        ├── 2. AI vs AI Autoplay (Pacman AI với ma AI)
        |   ├── Chọn map (Tiny, Medium, Big)
        ├── 3. Discovery mode (Tìm kiếm đường đi)
            ├── Tìm đường ăn 1 mồi
            |   ├── Chọn map (Tiny, Medium, Big, Map cụt)
            |   ├── Chọn thuật toán (A*, BFS, UCS, Greedy, DFS)
            ├── Tìm đường ăn nhiều mồi
                ├── Chọn map (Tiny, Medium, Big, Map cụt)
                ├── Chọn thuật toán (A*, BFS, UCS, Greedy, DFS)
```

**5.3. Các chế độ**
1. Player vs AI Ghosts (Người chơi với ma AI): Người chơi điều khiển pacman bằng nút lên xuống, né ma (ma sẽ đuổi theo pacman bằng ChaseGhost)
2. AI vs AI Autoplay (Pacman AI với ma AI): Pacman tự chơi bằng thuật toán Alpha-Beta (độ sâu 1), ma đuổi theo bằng ChaseGhost. Thanh trên cùng hiển thị tác tử, độ sâu, số nút đã xét, thời gian ra quyết định.
3. Discovery mode (Tìm kiếm đường đi): Không có ma. Chọn một thuật toán tìm đường, game bắt đầu ở trạng thái tạm dừng, ấn nút [Resume] (Phím Space) để bắt đầu tìm kiếm, khi này màn hình hiển thị quá trình quét (ô xanh), quét xong sẽ hiện đường đi tìm được (ô vàng), sau đó ấn phím Space để Pacman bắt đầu đi theo đường đó. Có bản đồ "Unreachable" để xem trường hợp không có đường đi.

**5.4. Điều khiển trong game**
| Phím / Nút | Tác dụng |
| --- | --- |
| Mũi tên di duyển | Để điều khiển Pacman trong chế độ 1 |
| Nút pause (Phím Space) | Tạm dừng trò chơi |
| Nút step (Phím S) | Đi 1 bước khi đang tạm dừng (ở chế độ tìm kiếm đường đi là quét thêm một ô) |
| Nút restart (Phím R) | Chơi lại |
| ESC | Quay về màn hình chính (Start / Exit) |

### VI. Cách chạy từng thuật toán
**Cách 1:** Qua giao diện menu (Chọn chế độ 3, tìm kiếm đường đi, chọn số lượng mục tiêu tìm kiếm rồi chọn thuật toán)
**Cách 2:** Chạy code trong thư mục chính
```
from maps.map_generator import load_map
from src.search import breadth_first_search, a_star_search
from src.searchAgents import PositionSearchProblem, manhattan_heuristic

```
