"""
player.py — Gestion du joueur (Tiny Wings)

Objectif "feel" Tiny Wings :
- Maintien ESPACE = boost (mais contrôlé, pas "fusil")
- Montée (pente négative) = décélération naturelle (gravité qui tire)
- Descente (pente positive) = légère accélération
- Tap ESPACE = saut (jusqu'à 3)
- Squash & stretch à l'impact + bille lisible (contour + highlight)
"""

import pygame

GRAVITY = 1800.0  # px/s²


class Player:
    """Joueur (bille) : saut multi-impulsions + boost contrôlé, avec freinage en montée."""

    def __init__(self, x_screen: float, radius: int):
        self.x = float(x_screen)
        self.y = 100.0
        self.radius = int(radius)

        # Vitesses (vx pilote le scrolling dans main)
        self.vx = 180.0
        self.vy = 0.0

        self.state = "VOL"

        # Input
        self.space_prev = False
        self.boosting = False

        # Triple saut (tap)
        self.jump_count = 0
        self.jump_max = 3
        self.jump_strength = 430.0
        self.jump_decay = 0.78

        # Energy (0..2)
        self.energy = 0.0

        # vitesse min/max
        self.vx_min = 90.0
        self.vx_max = 520.0  # ↓ réduit pour éviter l'effet "fusil" (ajuste si besoin)

        # Impact / squash
        self.impact_timer = 0.0
        self.impact_strength = 0.0

        # Air time (pour score x2)
        self.air_time = 0.0

        # Mémoire terrain
        self._last_ground_y = None
        self.prev_slope = 0.0

        # Tuning "feel"
        self.boost_gain = 0.55     # charge d'énergie (plus petit => boost moins violent)
        self.base_charge = 0.06    # charge minimale
        self.uphill_drag = 320.0   # freinage en montée (plus grand => montée plus dure)
        self.downhill_push = 160.0 # petit push en descente
        self.boost_push = 200.0    # conversion énergie -> vx (plus petit => moins violent)
        self.friction = 0.08       # friction globale

    def update(self, dt: float, terrain) -> None:
        keys = pygame.key.get_pressed()
        space = bool(keys[pygame.K_SPACE])
        space_pressed = space and (not self.space_prev)
        self.space_prev = space
        self.boosting = space

        ground_y = terrain.get_height_screen_x(self.x)
        slope = terrain.get_slope_screen_x(self.x)  # dy/dx (y vers le bas)

        if self._last_ground_y is None:
            self._last_ground_y = ground_y
        ground_vy = (ground_y - self._last_ground_y) / dt

        # timer impact
        if self.impact_timer > 0.0:
            self.impact_timer -= dt
            if self.impact_timer < 0.0:
                self.impact_timer = 0.0

        # gravité (un peu plus forte en boost)
        g = GRAVITY * (1.15 if self.boosting else 1.0)

        uphill = max(0.0, -slope)    # pente négative => montée
        downhill = max(0.0, slope)   # pente positive => descente

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

            # Energy : charge surtout en descente, un peu en continu si boost
            if self.boosting:
                charge = self.base_charge + self.boost_gain * downhill
                self.energy += charge * dt
            else:
                # sans action, l'énergie redescend
                self.energy -= 0.40 * dt

            self.energy = max(0.0, min(2.0, self.energy))

            # --------- vx "Tiny Wings feel" ----------
            # 1) Boost doux (pas fusil)
            self.vx += (self.boost_push * self.energy) * dt

            # 2) Montée = freinage fort
            self.vx -= (self.uphill_drag * uphill) * dt

            # 3) Descente = petit push naturel
            self.vx += (self.downhill_push * downhill) * dt

            # 4) friction globale
            self.vx *= (1.0 - self.friction * dt)

            # clamp
            self.vx = max(self.vx_min, min(self.vx_max, self.vx))

            # recoller au sol si toujours SOL
            if self.state == "SOL":
                self.y = ground_y - self.radius
                self.vy = ground_vy

            # rebond crête (relâché = plus de vol)
            if (not self.boosting) and (self.prev_slope < -0.05) and (slope > 0.05) and (self.vx > 130):
                self.state = "VOL"
                self.vy = -0.45 * self.vx
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
        """Dessine la bille (lisible) + squash à l'impact."""
        # couleur
        if self.boosting:
            color = (35, 35, 35)
        else:
            color = (230, 60, 60) if self.state == "VOL" else (40, 80, 240)

        r = self.radius
        w = h = int(r * 2)

        # "s'affaisse" en boost
        if self.boosting:
            w = int(r * 2.15)
            h = int(r * 1.65)

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

        # highlight blanc (effet “bille”)
        highlight = rect.copy()
        highlight.width = int(rect.width * 0.35)
        highlight.height = int(rect.height * 0.35)
        highlight.center = (
            rect.centerx - int(rect.width * 0.18),
            rect.centery - int(rect.height * 0.18)
        )
        pygame.draw.ellipse(screen, (255, 255, 255), highlight)