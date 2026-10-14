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
```terminal
    py main.py
```
**5.2. Menu**
- Trong giao diện Menu, ấn mũi tên lên xuống để chọn, Enter để xác nhận, hoặc có thể dùng chuột, ấn Back để quay trở lại màn hình trước.
- Luồng: Màn hình chính (Start / Exit) --> Chọn chế độ chơi --> Chọn kích thước bản đồ

**5.3. Các chế độ**
1. 
2. 
3. 

**5.4. Điều khiển trong game**
| Phím / Nút | Tác dụng |
| --- | --- |
| Mũi tên di duyển | Để điều khiển Pacman trong chế độ người chơi |
| 