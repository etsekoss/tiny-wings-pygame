"""
player.py — Gestion du joueur (Tiny Wings)

- ESPACE (tap) : saut (jusqu'à 3)
- ESPACE (maintien) : boost (gravité légèrement plus forte + charge d'énergie)
- vx pilote le scrolling (le joueur reste fixe en X à l'écran)
- Squash & stretch à l'impact
"""

import pygame

GRAVITY = 1800.0  # px/s²


class Player:
    """Joueur (bille) : saut multi-impulsions + boost, avec physique simple et stable."""

    def __init__(self, x_screen: float, radius: int):
        """
        x_screen : position X fixe à l'écran
        radius   : rayon de la bille (px)
        """
        self.x = float(x_screen)
        self.y = 100.0
        self.radius = int(radius)

        # Vitesses (vx pilote le scrolling dans main)
        self.vx = 180.0
        self.vy = 0.0

        # Etat : "SOL" / "VOL"
        self.state = "VOL"

        # Input
        self.space_prev = False
        self.boosting = False

        # Triple saut (tap)
        self.jump_count = 0
        self.jump_max = 3
        self.jump_strength = 430.0
        self.jump_decay = 0.78

        # Energy (0..2) -> boost de vx
        self.energy = 0.0
        self.vx_min = 90.0
        self.vx_max = 650.0

        # Impact / squash
        self.impact_timer = 0.0
        self.impact_strength = 0.0

        # Air time (utilisé pour le score x2)
        self.air_time = 0.0

        # Mémoire terrain (pour ground_vy)
        self._last_ground_y = None
        self.prev_slope = 0.0

    def update(self, dt: float, terrain) -> None:
        """
        Met à jour la physique du joueur.
        - Tap espace : saut (jusqu'à 3)
        - Maintien espace : boost (charge énergie) + gravité légèrement augmentée
        - Collisions sol : via terrain.get_height_screen_x (pas de Rect)
        """
        keys = pygame.key.get_pressed()
        space = bool(keys[pygame.K_SPACE])
        space_pressed = space and (not self.space_prev)  # edge
        self.space_prev = space
        self.boosting = space

        ground_y = terrain.get_height_screen_x(self.x)
        slope = terrain.get_slope_screen_x(self.x)

        if self._last_ground_y is None:
            self._last_ground_y = ground_y
        ground_vy = (ground_y - self._last_ground_y) / dt

        # timer impact
        if self.impact_timer > 0.0:
            self.impact_timer -= dt
            if self.impact_timer < 0.0:
                self.impact_timer = 0.0

        # gravité (un peu plus forte en boost)
        g = GRAVITY * (1.25 if self.boosting else 1.0)

        # -------------------
        # SOL
        # -------------------
        if self.state == "SOL":
            # reset au sol
            self.jump_count = 0
            self.air_time = 0.0

            # Tap = saut
            if space_pressed:
                self.state = "VOL"
                self.vy = -self.jump_strength
                self.jump_count = 1
                self.y -= 2.0

            # Energy : charge (boost) / décharge (si on ne joue pas)
            if self.boosting:
                charge = 0.9 * max(0.0, slope) + 0.12
                self.energy += charge * dt
            else:
                self.energy -= 0.55 * dt

            self.energy = max(0.0, min(2.0, self.energy))

            # vx pilotée par l'énergie
            self.vx += (900.0 * self.energy) * dt

            # friction légère (pas d'arrêt brutal)
            self.vx *= (1.0 - 0.10 * dt)

            # clamp
            self.vx = max(self.vx_min, min(self.vx_max, self.vx))

            # recoller au sol si on est toujours en SOL
            if self.state == "SOL":
                self.y = ground_y - self.radius
                self.vy = ground_vy

            # rebond crête (relâché = plus de vol)
            if (not self.boosting) and (self.prev_slope < -0.05) and (slope > 0.05) and (self.vx > 140):
                self.state = "VOL"
                self.vy = -0.50 * self.vx
                self.y = (ground_y - self.radius) - 2.0

        # -------------------
        # VOL
        # -------------------
        else:
            # Tap en l'air => saut supplémentaire (jusqu'à 3)
            if space_pressed and self.jump_count < self.jump_max:
                k = self.jump_count
                strength = self.jump_strength * (self.jump_decay ** k)
                self.vy = min(self.vy, 0.0) - strength
                self.jump_count += 1

            # intégration
            self.vy += g * dt
            self.y += self.vy * dt
            self.air_time += dt

            # atterrissage
            if self.vy >= 0 and self.y + self.radius >= ground_y:
                impact_vy = self.vy
                self.y = ground_y - self.radius
                self.vy = 0.0
                self.state = "SOL"

                # squash violent
                if impact_vy > 900.0:
                    self.impact_timer = 0.12
                    self.impact_strength = min(impact_vy / 1800.0, 1.0)
                else:
                    self.impact_strength = 0.0

        self._last_ground_y = ground_y
        self.prev_slope = slope

    def draw(self, screen) -> None:
        """Dessine la bille (couleur selon état) + squash à l'impact."""
        # couleur
        if self.boosting:
            color = (30, 30, 30)
        else:
            color = (220, 50, 50) if self.state == "VOL" else (50, 50, 220)

        r = self.radius
        w = h = int(r * 2)

        # "s'affaisse" 
        if self.boosting:
            w = int(r * 2.2)
            h = int(r * 1.6)

        # squash d'impact violent
        if self.impact_timer > 0.0:
            squash = 0.35 * self.impact_strength
            w = int(w * (1.0 + squash))
            h = int(h * (1.0 - squash))

        rect = pygame.Rect(0, 0, w, h)
        rect.center = (int(self.x), int(self.y))
        # ellipse principale
        pygame.draw.ellipse(screen, color, rect)

        # contour noir (lisibilité)
        pygame.draw.ellipse(screen, (0, 0, 0), rect, 3)

        # petit highlight blanc (effet “bille”)
        highlight = rect.copy()
        highlight.width = int(rect.width * 0.35)
        highlight.height = int(rect.height * 0.35)
        highlight.center = (
            rect.centerx - int(rect.width * 0.18),
            rect.centery - int(rect.height * 0.18)
        )
        pygame.draw.ellipse(screen, (255, 255, 255), highlight)