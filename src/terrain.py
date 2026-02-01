"""
terrain.py — Génération et rendu du terrain

- Terrain "infini" généré par somme de sinusoïdes.
- Scrolling : fenêtre glissante de points (pas de mémoire infinie).
- get_height_screen_x : hauteur par interpolation linéaire.
- Gaps optionnels : trous réels (vide) + rampes, avec randomisation.
"""

import math
import random
import pygame
from typing import List, Tuple


class Terrain:
    """Terrain infini (sinus) + trous optionnels, exploité via get_height_screen_x et get_slope_screen_x."""

    def __init__(self, width: int, height: int, dx: int = 20, base_y_ratio: float = 0.75):
        self.width = width
        self.height = height
        self.dx = dx

        self.base_y = int(height * base_y_ratio)

        # Random generator (seed aléatoire par run)
        self.rng = random.Random()

        # Multi-biomes
        self.waves_base: List[Tuple[float, float]] = [(85, 0.010), (45, 0.023), (22, 0.045)]
        self.waves_max:  List[Tuple[float, float]] = [(95, 0.016), (55, 0.035), (28, 0.070)]
        self.waves: List[Tuple[float, float]] = list(self.waves_base)

        # Gaps (trous)
        self.gaps_enabled = False
        self.gaps: List[Tuple[float, float]] = []

        self.gap_every = 2200.0
        self.gap_width = 180.0
        self.gap_ramp = 200.0

        # Premier trou : RANDOM pour éviter "mêmes obstacles à chaque run"
        self.next_gap_wx = self.rng.uniform(600.0, 1600.0)

        # Coordonnée monde du bord gauche affiché
        self.world_x0 = 0.0

        # Points écran
        self.points: List[List[float]] = []
        self._init_points()

    def reset_gaps(self) -> None:
        """Réinitialise complètement la séquence de trous (utile si tu veux un nouveau pattern)."""
        self.gaps = []
        self.next_gap_wx = self.rng.uniform(self.world_x0 + 600.0, self.world_x0 + 1600.0)

    def set_biome(self, t: float) -> None:
        """Interpole les paramètres sinusoïdaux selon t in [0,1]."""
        t = max(0.0, min(1.0, t))
        new_waves = []
        for (a0, f0), (a1, f1) in zip(self.waves_base, self.waves_max):
            amp = a0 + (a1 - a0) * t
            freq = f0 + (f1 - f0) * t
            new_waves.append((amp, freq))
        self.waves = new_waves

    def _spawn_gaps_until(self, max_world_x: float) -> None:
        """Ajoute des trous à l'avance jusqu'à max_world_x (coord monde), avec randomisation."""
        if not self.gaps_enabled:
            return

        while self.next_gap_wx < max_world_x:
            start = self.next_gap_wx

            # randomisation autour des réglages courants
            width = self.rng.uniform(self.gap_width * 0.7, self.gap_width * 1.3)
            every = self.rng.uniform(self.gap_every * 0.7, self.gap_every * 1.3)

            end = start + width
            self.gaps.append((start, end))
            self.next_gap_wx += every

        # nettoyage
        cutoff = self.world_x0 - 2000.0
        if cutoff > 0:
            self.gaps = [(a, b) for (a, b) in self.gaps if b >= cutoff]

    def height_at_world(self, world_x: float) -> float:
        """Hauteur du sol (y écran) pour une abscisse monde."""
        # hauteur normale
        normal_y = self.base_y
        for amp, freq in self.waves:
            normal_y += amp * math.sin(world_x * freq)

        # trous réels (vide) + rampes
        if self.gaps_enabled:
            hole_y = self.height + 250
            for a, b in self.gaps:
                r = self.gap_ramp

                if a - r <= world_x < a:
                    t = (world_x - (a - r)) / r
                    return normal_y * (1 - t) + hole_y * t

                if a <= world_x <= b:
                    return hole_y

                if b < world_x <= b + r:
                    t = (world_x - b) / r
                    return hole_y * (1 - t) + normal_y * t

        return normal_y

    def get_height_screen_x(self, x_screen: float) -> float:
        """Hauteur du sol à x_screen par interpolation linéaire."""
        if x_screen <= self.points[0][0]:
            return float(self.points[0][1])
        if x_screen >= self.points[-1][0]:
            return float(self.points[-1][1])

        i = int((x_screen - self.points[0][0]) // self.dx)
        i = max(0, min(i, len(self.points) - 2))

        x0, y0 = self.points[i]
        x1, y1 = self.points[i + 1]

        if x1 == x0:
            return float(y0)

        t = (x_screen - x0) / (x1 - x0)
        return float(y0 + t * (y1 - y0))

    def get_slope_screen_x(self, x_screen: float) -> float:
        """Pente dy/dx approximée près de x_screen."""
        if x_screen <= self.points[0][0]:
            x0, y0 = self.points[0]
            x1, y1 = self.points[1]
        elif x_screen >= self.points[-1][0]:
            x0, y0 = self.points[-2]
            x1, y1 = self.points[-1]
        else:
            i = int((x_screen - self.points[0][0]) // self.dx)
            i = max(0, min(i, len(self.points) - 2))
            x0, y0 = self.points[i]
            x1, y1 = self.points[i + 1]

        if x1 == x0:
            return 0.0
        return float((y1 - y0) / (x1 - x0))

    def _init_points(self) -> None:
        """Initialise les points couvrant la largeur écran."""
        n = self.width // self.dx + 3
        self.points = []
        for i in range(n):
            world_x = self.world_x0 + i * self.dx
            self._spawn_gaps_until(world_x + 3000.0)
            y = self.height_at_world(world_x)
            x_screen = i * self.dx
            self.points.append([x_screen, y])

    def update_scroll(self, scroll_speed_px: float) -> None:
        """Défilement : décale points, pop gauche, append droite."""
        for p in self.points:
            p[0] -= scroll_speed_px

        while len(self.points) > 0 and self.points[0][0] < -self.dx:
            self.points.pop(0)
            self.world_x0 += self.dx

        while len(self.points) < (self.width // self.dx + 3) or self.points[-1][0] < self.width + self.dx:
            last_x = self.points[-1][0]
            new_x = last_x + self.dx
            i = new_x / self.dx
            world_x = self.world_x0 + i * self.dx

            self._spawn_gaps_until(world_x + 3000.0)
            y = self.height_at_world(world_x)
            self.points.append([new_x, y])

    def draw(self, screen, color_ground, color_outline=None) -> None:
        """Dessine le sol via polygon."""
        poly = self.points[:]
        poly.append([self.points[-1][0], self.height])
        poly.append([self.points[0][0], self.height])

        pygame.draw.polygon(screen, color_ground, poly)
        if color_outline is not None:
            pygame.draw.lines(screen, color_outline, False, self.points, 3)
    
    def set_waves(self, waves):
        """Override direct des sinusoïdes (amp, freq)."""
        self.waves = list(waves)