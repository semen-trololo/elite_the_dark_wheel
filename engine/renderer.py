"""
engine/renderer.py
Wireframe 3D рендерер для отрисовки объектов в стиле Elite.
"""

import math
from engine.math3d import Vector3


class Mesh:
    """3D модель, состоящая из вершин и рёбер."""
    
    def __init__(self, vertices, edges):
        """
        vertices: список Vector3 - координаты вершин
        edges: список кортежей (index1, index2) - рёбра между вершинами
        """
        self.vertices = vertices
        self.edges = edges


class WireframeRenderer:
    """Рендерер для отрисовки wireframe 3D объектов на 2D экране."""
    
    def __init__(self, screen_width, screen_height, fov=90):
        """
        screen_width: ширина экрана в пикселях
        screen_height: высота экрана в пикселях
        fov: поле зрения (field of view) в градусах
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.fov = fov
        self.center_x = screen_width / 2
        self.center_y = screen_height / 2
    
    def project(self, point: Vector3):
        """
        Проецирует 3D точку на 2D экран с правильной перспективой.
        """
        # Если точка за камерой или слишком близко - не проецируем
        if point.z <= 0.1:
            return None
        
        # Классическая перспективная проекция
        # self.fov теперь играет роль focal_length (фокусного расстояния)
        # Чем больше fov, тем сильнее "зум" (объекты крупнее)
        scale = self.fov / point.z
        
        screen_x = (point.x * scale) + self.center_x
        # ВАЖНО: Инвертируем Y! В pygame ось Y направлена ВНИЗ, 
        # а в 3D пространстве - ВВЕРХ. Без этого корабль будет перевёрнут.
        screen_y = -(point.y * scale) + self.center_y 
        
        return (int(screen_x), int(screen_y))
    
    def render_mesh(self, mesh: Mesh, position: Vector3 = None, rotation_matrix=None):
        """
        Отрисовывает меш на экране.
        
        mesh: объект Mesh для отрисовки
        position: Vector3 - позиция объекта в мире (пока не используется)
        rotation_matrix: Matrix3x3 - матрица поворота (пока не используется)
        
        Возвращает список линий для отрисовки: [(x1, y1, x2, y2), ...]
        """
        lines = []
        
        for edge in mesh.edges:
            v1_idx, v2_idx = edge
            
            # Получаем вершины
            v1 = mesh.vertices[v1_idx]
            v2 = mesh.vertices[v2_idx]
            
            # Применяем трансформации (если есть)
            if rotation_matrix:
                v1 = rotation_matrix * v1
                v2 = rotation_matrix * v2
            
            if position:
                v1 = v1 + position
                v2 = v2 + position
            
            # Проецируем на экран
            p1 = self.project(v1)
            p2 = self.project(v2)
            
            # Если обе точки видны - добавляем линию
            if p1 and p2:
                lines.append((p1[0], p1[1], p2[0], p2[1]))
        
        return lines