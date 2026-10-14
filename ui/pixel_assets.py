# Bảng mã màu dùng chung

SIZE = 24
LE_TREN = 72
LE_DUOI = 46
WIDTH, HEIGHT = 600, 500

COLORS = {
    'Y': (255, 245, 59),
    'G': (254, 207, 54),
    'W': (255, 255, 255),
    'P': (253, 138, 209),
    'O': (249, 122, 75),
    'R': (253, 46, 67),
    'B': (72, 227, 253),
    'BL': (15, 84, 252),
    'BG': (3, 3, 3),
    'D': (0, 0, 0),
    'MUD':(110, 68, 30),
    'MUD_TXT':(220, 180, 120)
}

P_OPEN = [
    " YYY",
    "YYY ",
    "YY  ",
    "YYY ",
    " YYY"
]

P_CLOSED = [
    " YY ",
    "YYYY",
    "YYYY",
    "YYYY",
    " YY ",
]

'''
PACMAN_MID_RIGHT = [
"       YYYYYYY       ",
"     YYYYYYYYYYY     ",
"    YYYYYYYYYYYYYY   ",
"   YYYYYYYYYYYYYYYY  ",
"  YYYYYYYYYYYYYYYYYY ",
" YYYYYYYYYYYYYYYYYYY ",
" YYYYYYYYYYYYYYYYYYYY",
"YYYYYYYYYYYYYYYYYYYYY",
"YYYYYYYYYYYYYYYYY    ",
"YYYYYYYYYYYYYY       ",
"YYYYYYYYYYY          ",
"YYYYYYYYYYYYYY       ",
"YYYYYYYYYYYYYYYYY    ",
"YYYYYYYYYYYYYYYYYYYYY",
" YYYYYYYYYYYYYYYYYYYY",
" YYYYYYYYYYYYYYYYYYY ",
"  YYYYYYYYYYYYYYYYYY ",
"   YYYYYYYYYYYYYYYY  ",
"    YYYYYYYYYYYYYY   ",
"     YYYYYYYYYYY     ",
"       YYYYYYY       ",
]
PACMAN_CLOSED = [
"       YYYYYYY       ",
"     YYYYYYYYYYY     ",
"    YYYYYYYYYYYYY    ",
"   YYYYYYYYYYYYYYY   ",
"  YYYYYYYYYYYYYYYYY  ",
" YYYYYYYYYYYYYYYYYYY ",
" YYYYYYYYYYYYYYYYYYY ",
"YYYYYYYYYYYYYYYYYYYYY",
"YYYYYYYYYYYYYYYYYYYYY",
"YYYYYYYYYYYYYYYYYYYYY",
"YYYYYYYYYYYYYYYYYYYYY",
"YYYYYYYYYYYYYYYYYYYYY",
"YYYYYYYYYYYYYYYYYYYYY",
"YYYYYYYYYYYYYYYYYYYYY",
" YYYYYYYYYYYYYYYYYYY ",
" YYYYYYYYYYYYYYYYYYY ",
"  YYYYYYYYYYYYYYYYY  ",
"   YYYYYYYYYYYYYYY   ",
"   YYYYYYYYYYYYYYY   ",
"     YYYYYYYYYYY     ",
"       YYYYYYY       ",

]
'''

GOAL1 = [
    " G ",
    "GGG",
    " G "
]
GOAL2 = [
    "W"
]

GHOST_PINK = [
    " PPP ",
    "PWPWP",
    "PPPPP",
    "PPPPP",
    "P P P",
]

GHOST_ORANGE = [
    " OOO ",
    "OWOWO",
    "OOOOO",
    "OOOOO",
    "O O O",
]

GHOST_BLUE = [
    " BBB ",
    "BWBWB",
    "BBBBB",
    "BBBBB",
    "B B B",
]

GHOST_RED = [
    " RRR ",
    "RWRWR",
    "RRRRR",
    "RRRRR",
    "R R R",
]

GHOST_EAT = [
    " WWW ",
    "WDWDW",
    "WWWWW",
    "WWWWW",
    "W W W",
]

GHOST_ATE = [
    " WWW ",
    "WDDDW",
    "WDWDW",
    "WDDDW",
    " WWW "
]

WALL = [
    'BL'
]