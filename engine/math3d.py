"""
engine/math3d.py
Математическое ядро для 3D пространства.
Векторы, матрицы и проекции для wireframe рендерера.
"""

import math


class Vector3:
    """3D вектор для позиций, скоростей и направлений."""
    
    __slots__ = ['x', 'y', 'z']  # Оптимизация памяти
    
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
    
    def __add__(self, other):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar):
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def __rmul__(self, scalar):
        return self.__mul__(scalar)
    
    def __repr__(self):
        return f"Vector3({self.x}, {self.y}, {self.z})"
    
    def magnitude(self):
        """Длина вектора."""
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)
    
    def normalize(self):
        """Возвращает единичный вектор (направление)."""
        mag = self.magnitude()
        if mag == 0:
            return Vector3(0, 0, 0)
        return Vector3(self.x / mag, self.y / mag, self.z / mag)
    
    def dot(self, other):
        """Скалярное произведение."""
        return self.x * other.x + self.y * other.y + self.z * other.z
    
    def cross(self, other):
        """Векторное произведение."""
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )


class Matrix3x3:
    """Матрица 3x3 для поворотов и трансформаций."""
    
    def __init__(self, data=None):
        if data is None:
            # Единичная матрица по умолчанию
            self.data = [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0]
            ]
        else:
            self.data = data
    
    @staticmethod
    def identity():
        """Создаёт единичную матрицу."""
        return Matrix3x3()
    
    @staticmethod
    def rotation_x(angle):
        """Матрица поворота вокруг оси X."""
        c = math.cos(angle)
        s = math.sin(angle)
        return Matrix3x3([
            [1.0, 0.0, 0.0],
            [0.0, c, s],
            [0.0, -s, c]
        ])
    
    @staticmethod
    def rotation_y(angle):
        """Матрица поворота вокруг оси Y."""
        c = math.cos(angle)
        s = math.sin(angle)
        return Matrix3x3([
            [c, 0.0, -s],
            [0.0, 1.0, 0.0],
            [s, 0.0, c]
        ])
    
    @staticmethod
    def rotation_z(angle):
        """Матрица поворота вокруг оси Z."""
        c = math.cos(angle)
        s = math.sin(angle)
        return Matrix3x3([
            [c, -s, 0.0],
            [s, c, 0.0],
            [0.0, 0.0, 1.0]
        ])
    
    def __mul__(self, other):
        """Умножение матрицы на вектор или другую матрицу."""
        if isinstance(other, Vector3):
            # Матрица * Вектор
            x = self.data[0][0] * other.x + self.data[0][1] * other.y + self.data[0][2] * other.z
            y = self.data[1][0] * other.x + self.data[1][1] * other.y + self.data[1][2] * other.z
            z = self.data[2][0] * other.x + self.data[2][1] * other.y + self.data[2][2] * other.z
            return Vector3(x, y, z)
        elif isinstance(other, Matrix3x3):
            # Матрица * Матрица
            result = [[0.0] * 3 for _ in range(3)]
            for i in range(3):
                for j in range(3):
                    for k in range(3):
                        result[i][j] += self.data[i][k] * other.data[k][j]
            return Matrix3x3(result)
        else:
            raise TypeError(f"Cannot multiply Matrix3x3 by {type(other)}")
    
    def __repr__(self):
        return f"Matrix3x3({self.data})"