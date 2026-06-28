import unittest
import math
from engine.math3d import Vector3, Matrix3x3

class TestVector3(unittest.TestCase):
    
    def test_creation(self):
        v = Vector3(1, 2, 3)
        self.assertEqual(v.x, 1)
        self.assertEqual(v.y, 2)
        self.assertEqual(v.z, 3)
    
    def test_addition(self):
        v1 = Vector3(1, 2, 3)
        v2 = Vector3(4, 5, 6)
        result = v1 + v2
        self.assertEqual(result.x, 5)
        self.assertEqual(result.y, 7)
        self.assertEqual(result.z, 9)
    
    def test_subtraction(self):
        v1 = Vector3(5, 7, 9)
        v2 = Vector3(1, 2, 3)
        result = v1 - v2
        self.assertEqual(result.x, 4)
        self.assertEqual(result.y, 5)
        self.assertEqual(result.z, 6)
    
    def test_scalar_multiplication(self):
        v = Vector3(1, 2, 3)
        result = v * 2
        self.assertEqual(result.x, 2)
        self.assertEqual(result.y, 4)
        self.assertEqual(result.z, 6)
    
    def test_magnitude(self):
        v = Vector3(3, 4, 0)
        self.assertAlmostEqual(v.magnitude(), 5.0)
    
    def test_normalize(self):
        v = Vector3(3, 4, 0)
        normalized = v.normalize()
        self.assertAlmostEqual(normalized.magnitude(), 1.0)
        self.assertAlmostEqual(normalized.x, 0.6)
        self.assertAlmostEqual(normalized.y, 0.8)
    
    def test_dot_product(self):
        v1 = Vector3(1, 2, 3)
        v2 = Vector3(4, 5, 6)
        result = v1.dot(v2)
        self.assertEqual(result, 32)  # 1*4 + 2*5 + 3*6
    
    def test_cross_product(self):
        v1 = Vector3(1, 0, 0)
        v2 = Vector3(0, 1, 0)
        result = v1.cross(v2)
        self.assertEqual(result.x, 0)
        self.assertEqual(result.y, 0)
        self.assertEqual(result.z, 1)


class TestMatrix3x3(unittest.TestCase):
    
    def test_identity(self):
        m = Matrix3x3.identity()
        v = Vector3(1, 2, 3)
        result = m * v
        self.assertEqual(result.x, 1)
        self.assertEqual(result.y, 2)
        self.assertEqual(result.z, 3)
    
    def test_rotation_x(self):
        m = Matrix3x3.rotation_x(math.pi / 2)  # 90 градусов
        v = Vector3(0, 1, 0)
        result = m * v
        self.assertAlmostEqual(result.x, 0, places=5)
        self.assertAlmostEqual(result.y, 0, places=5)
        self.assertAlmostEqual(result.z, -1, places=5)
    
    def test_rotation_y(self):
        m = Matrix3x3.rotation_y(math.pi / 2)  # 90 градусов
        v = Vector3(1, 0, 0)
        result = m * v
        self.assertAlmostEqual(result.x, 0, places=5)
        self.assertAlmostEqual(result.y, 0, places=5)
        self.assertAlmostEqual(result.z, 1, places=5)
    
    def test_rotation_z(self):
        m = Matrix3x3.rotation_z(math.pi / 2)  # 90 градусов
        v = Vector3(1, 0, 0)
        result = m * v
        self.assertAlmostEqual(result.x, 0, places=5)
        self.assertAlmostEqual(result.y, 1, places=5)
        self.assertAlmostEqual(result.z, 0, places=5)


if __name__ == '__main__':
    unittest.main()