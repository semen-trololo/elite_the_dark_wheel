import unittest
import math
from engine.math3d import Vector3, Matrix3x3
from engine.renderer import WireframeRenderer, Mesh


class TestMesh(unittest.TestCase):
    
    def test_mesh_creation(self):
        vertices = [Vector3(0, 0, 0), Vector3(1, 0, 0), Vector3(0, 1, 0)]
        edges = [(0, 1), (1, 2), (2, 0)]
        mesh = Mesh(vertices, edges)
        self.assertEqual(len(mesh.vertices), 3)
        self.assertEqual(len(mesh.edges), 3)


class TestProjection(unittest.TestCase):
    
    def setUp(self):
        # Создаём рендерер с экраном 800x600
        self.renderer = WireframeRenderer(800, 600)
    
    def test_project_point_at_center(self):
        # Точка прямо перед камерой на расстоянии 10
        point = Vector3(0, 0, 10)
        screen_x, screen_y = self.renderer.project(point)
        # Должна быть в центре экрана
        self.assertAlmostEqual(screen_x, 400, places=0)
        self.assertAlmostEqual(screen_y, 300, places=0)
    
    def test_project_point_to_the_right(self):
        # Точка справа от центра
        point = Vector3(5, 0, 10)
        screen_x, screen_y = self.renderer.project(point)
        # Должна быть правее центра
        self.assertGreater(screen_x, 400)
        self.assertAlmostEqual(screen_y, 300, places=0)
    
    def test_project_point_closer_is_larger(self):
        # Точка ближе к камере должна проецироваться дальше от центра
        # Используем большие значения x, чтобы разница была заметной после округления
        point_far = Vector3(20, 0, 20)
        point_near = Vector3(20, 0, 10)
        
        x_far, _ = self.renderer.project(point_far)
        x_near, _ = self.renderer.project(point_near)
        
        # Ближняя точка должна быть дальше от центра (400)
        self.assertGreater(abs(x_near - 400), abs(x_far - 400))
    
    def test_project_point_behind_camera(self):
        # Точка за камерой не должна проецироваться
        point = Vector3(0, 0, -5)
        result = self.renderer.project(point)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()