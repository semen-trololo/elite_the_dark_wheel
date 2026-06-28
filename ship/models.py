"""
ship/models.py
3D модели кораблей в стиле Elite (wireframe).
"""

from engine.math3d import Vector3
from engine.renderer import Mesh


def create_sidewinder() -> Mesh:
    """
    Создаёт модель Sidewinder — первого пирата в Elite.
    Аутентичная плоская модель из оригинальной игры 1984 года.
    
    Ключевые особенности:
    - Корабль ОЧЕНЬ плоский (маленькая высота)
    - Нос - это ЛИНИЯ (2 точки), а не точка
    - Нет выраженного хвоста
    - Форма: трапеция/клин
    """
    
    # Вершины Sidewinder (ПЛОСКАЯ модель)
    # Высота по Y очень маленькая (0.2)
    
    # Нос - ЛИНИЯ (2 точки сверху и снизу)
    nose_top = Vector3(0, 0.2, -4)
    nose_bottom = Vector3(0, -0.2, -4)
    
    # Передние концы крыльев (самые широкие точки)
    left_wing_front = Vector3(-3, 0, -1)
    right_wing_front = Vector3(3, 0, -1)
    
    # Задние концы крыльев
    left_wing_back = Vector3(-2, 0, 2)
    right_wing_back = Vector3(2, 0, 2)
    
    # Верхняя и нижняя точки корпуса (для минимального объёма)
    top_center = Vector3(0, 0.2, 0)
    bottom_center = Vector3(0, -0.2, 0)
    
    # Задняя точка (не хвост, а просто конец корпуса)
    tail_top = Vector3(0, 0.15, 2.5)
    tail_bottom = Vector3(0, -0.15, 2.5)
    
    vertices = [
        nose_top,           # 0 - нос верх
        nose_bottom,        # 1 - нос низ
        left_wing_front,    # 2 - левое крыло перед
        right_wing_front,   # 3 - правое крыло перед
        left_wing_back,     # 4 - левое крыло зад
        right_wing_back,    # 5 - правое крыло зад
        top_center,         # 6 - верх корпуса
        bottom_center,      # 7 - низ корпуса
        tail_top,           # 8 - зад верх
        tail_bottom         # 9 - зад низ
    ]
    
    # Рёбра (соединения между вершинами)
    edges = [
        # Нос (линия)
        (0, 1),
        
        # Нос к крыльям
        (0, 2), (0, 3),
        (1, 2), (1, 3),
        
        # Нос к корпусу
        (0, 6), (1, 7),
        
        # Передняя кромка крыльев
        (2, 3),
        
        # Крылья к корпусу
        (2, 6), (2, 7),
        (3, 6), (3, 7),
        
        # Крылья к задней части
        (2, 4), (3, 5),
        
        # Задняя кромка крыльев
        (4, 5),
        
        # Корпус к крыльям сзади
        (4, 6), (4, 7),
        (5, 6), (5, 7),
        
        # Корпус к хвосту
        (6, 8), (6, 9),
        (7, 8), (7, 9),
        
        # Крылья к хвосту
        (4, 8), (4, 9),
        (5, 8), (5, 9),
        
        # Хвост (линия)
        (8, 9)
    ]
    
    return Mesh(vertices, edges)


def create_fighter_ship() -> Mesh:
    """Старая модель для совместимости."""
    nose = Vector3(0, 0, -3)
    front_top_left = Vector3(-1, 0.5, -1)
    front_top_right = Vector3(1, 0.5, -1)
    front_bottom_left = Vector3(-1, -0.5, -1)
    front_bottom_right = Vector3(1, -0.5, -1)
    back_top_left = Vector3(-1, 0.5, 1)
    back_top_right = Vector3(1, 0.5, 1)
    back_bottom_left = Vector3(-1, -0.5, 1)
    back_bottom_right = Vector3(1, -0.5, 1)
    tail = Vector3(0, 0, 3)
    
    vertices = [
        nose, front_top_left, front_top_right, front_bottom_left, front_bottom_right,
        back_top_left, back_top_right, back_bottom_left, back_bottom_right, tail
    ]
    
    edges = [
        (0, 1), (0, 2), (0, 3), (0, 4),
        (1, 2), (2, 4), (4, 3), (3, 1),
        (1, 5), (2, 6), (3, 7), (4, 8),
        (5, 6), (6, 8), (8, 7), (7, 5),
        (9, 5), (9, 6), (9, 7), (9, 8)
    ]
    
    return Mesh(vertices, edges)