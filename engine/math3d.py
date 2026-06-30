"""
engine/math3d.py
Математическое ядро для 3D пространства.
Векторы, матрицы и проекции для wireframe рендерера.

ИСПРАВЛЕНИЯ:
1. Добавлен __neg__ для операции -Vector3 (критично для автопилота!)
2. Добавлен __truediv__ для деления на скаляр
3. Добавлен __eq__ для сравнения векторов
4. Добавлен __iter__ для распаковки (x, y, z = vec)
5. Добавлен __abs__ как синоним magnitude()
6. Добавлен __bool__ — True если вектор ненулевой
7. Добавлены класс-методы Vector3.zero(), unit_x/y/z()
"""

import math
from typing import Iterator


class Vector3:
    """3D вектор для позиций, скоростей и направлений."""
    
    __slots__ = ['x', 'y', 'z']
    
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
    
    # =========================================================================
    # Класс-методы для создания стандартных векторов
    # =========================================================================
    @classmethod
    def zero(cls):
        """Нулевой вектор."""
        return cls(0.0, 0.0, 0.0)
    
    @classmethod
    def unit_x(cls):
        """Единичный вектор по X."""
        return cls(1.0, 0.0, 0.0)
    
    @classmethod
    def unit_y(cls):
        """Единичный вектор по Y."""
        return cls(0.0, 1.0, 0.0)
    
    @classmethod
    def unit_z(cls):
        """Единичный вектор по Z."""
        return cls(0.0, 0.0, 1.0)
    
    # =========================================================================
    # АРИФМЕТИЧЕСКИЕ ОПЕРАЦИИ
    # =========================================================================
    def __add__(self, other):
        if isinstance(other, Vector3):
            return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
        return NotImplemented
    
    def __sub__(self, other):
        if isinstance(other, Vector3):
            return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
        return NotImplemented
    
    def __mul__(self, scalar):
        if isinstance(scalar, (int, float)):
            return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)
        return NotImplemented
    
    def __rmul__(self, scalar):
        return self.__mul__(scalar)
    
    def __truediv__(self, scalar):
        """Деление на скаляр."""
        if isinstance(scalar, (int, float)):
            if scalar == 0:
                raise ZeroDivisionError("Vector3 division by zero")
            inv = 1.0 / scalar
            return Vector3(self.x * inv, self.y * inv, self.z * inv)
        return NotImplemented
    
    def __neg__(self):
        """Унарный минус: -Vector3. КРИТИЧНО для автопилота!"""
        return Vector3(-self.x, -self.y, -self.z)
    
    def __pos__(self):
        """Унарный плюс: +Vector3."""
        return Vector3(self.x, self.y, self.z)
    
    # =========================================================================
    # СРАВНЕНИЯ И ПРЕОБРАЗОВАНИЯ
    # =========================================================================
    def __eq__(self, other):
        if not isinstance(other, Vector3):
            return False
        return (self.x == other.x and self.y == other.y and self.z == other.z)
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __abs__(self):
        """abs(vec) возвращает длину вектора."""
        return self.magnitude()
    
    def __bool__(self):
        """Вектор истинен, если он ненулевой."""
        return (self.x != 0.0 or self.y != 0.0 or self.z != 0.0)
    
    def __iter__(self) -> Iterator[float]:
        """Позволяет распаковку: x, y, z = vec"""
        yield self.x
        yield self.y
        yield self.z
    
    def __len__(self) -> int:
        return 3
    
    def __getitem__(self, index: int) -> float:
        """Доступ по индексу: vec[0], vec[1], vec[2]"""
        if index == 0:
            return self.x
        elif index == 1:
            return self.y
        elif index == 2:
            return self.z
        raise IndexError(f"Vector3 index {index} out of range [0, 2]")
    
    def __repr__(self):
        return f"Vector3({self.x:.4f}, {self.y:.4f}, {self.z:.4f})"
    
    def __str__(self):
        return f"({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"
    
    # =========================================================================
    # ВЕКТОРНЫЕ ОПЕРАЦИИ
    # =========================================================================
    def magnitude(self) -> float:
        """Длина вектора."""
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)
    
    def magnitude_squared(self) -> float:
        """Квадрат длины (оптимизация - без sqrt)."""
        return self.x ** 2 + self.y ** 2 + self.z ** 2
    
    def normalize(self):
        """Возвращает единичный вектор (направление)."""
        mag = self.magnitude()
        if mag < 1e-10:
            return Vector3(0.0, 0.0, 0.0)
        inv_mag = 1.0 / mag
        return Vector3(self.x * inv_mag, self.y * inv_mag, self.z * inv_mag)
    
    def dot(self, other: 'Vector3') -> float:
        """Скалярное произведение."""
        return self.x * other.x + self.y * other.y + self.z * other.z
    
    def cross(self, other: 'Vector3') -> 'Vector3':
        """Векторное произведение."""
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )
    
    def distance_to(self, other: 'Vector3') -> float:
        """Расстояние до другого вектора."""
        return (self - other).magnitude()
    
    def distance_squared_to(self, other: 'Vector3') -> float:
        """Квадрат расстояния (оптимизация - без sqrt)."""
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return dx * dx + dy * dy + dz * dz
    
    def lerp(self, other: 'Vector3', t: float) -> 'Vector3':
        """Линейная интерполяция между двумя векторами (t от 0 до 1)."""
        return Vector3(
            self.x + (other.x - self.x) * t,
            self.y + (other.y - self.y) * t,
            self.z + (other.z - self.z) * t
        )
    
    def copy(self) -> 'Vector3':
        """Возвращает копию вектора."""
        return Vector3(self.x, self.y, self.z)


class Matrix3x3:
    """Матрица 3x3 для поворотов и трансформаций."""
    
    def __init__(self, data=None):
        if data is None:
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
            x = self.data[0][0] * other.x + self.data[0][1] * other.y + self.data[0][2] * other.z
            y = self.data[1][0] * other.x + self.data[1][1] * other.y + self.data[1][2] * other.z
            z = self.data[2][0] * other.x + self.data[2][1] * other.y + self.data[2][2] * other.z
            return Vector3(x, y, z)
        elif isinstance(other, Matrix3x3):
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