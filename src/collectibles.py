import math
import pygame

class CollectibleManager:
    """
    Gère des pièces/soleils en coordonnées 'monde' (world_x).
    Placement: y = get_height(x_screen) - offset.
    """
    def __init__(self, width, height, dx_world=500, y_offset=40):
        self.width = width
        self.height = height
        self.dx_world = dx_world      # espacement monde entre collectibles
        self.y_offset = y_offset
        self.items = []               # liste de dict: {"wx":..., "taken":False}
        self.next_spawn_wx = 800.0

    def update(self, distance_world, player_x_screen, terrain):
        """
        distance_world : distance parcourue (monde)
        terrain        : utilisé pour get_height_screen_x
        """
        # Spawn en avance
        while self.next_spawn_wx < distance_world + 2500:
            self.items.append({"wx": self.next_spawn_wx, "taken": False})
            self.next_spawn_wx += self.dx_world

        # Nettoyage
        cutoff = distance_world - 2000
        if len(self.items) > 0 and self.items[0]["wx"] < cutoff:
            # supprime les items très loin derrière
            self.items = [it for it in self.items if it["wx"] >= cutoff]

    def draw(self, screen, distance_world, player_x_screen, terrain):
        """Dessine les collectibles visibles."""
        for it in self.items:
            if it["taken"]:
                continue

            # conversion world->screen
            x_screen = player_x_screen + (it["wx"] - distance_world)

            if x_screen < -50 or x_screen > self.width + 50:
                continue

            y_ground = terrain.get_height_screen_x(x_screen)
            y = y_ground - self.y_offset

            # dessin simple (soleil/pièce)
            pygame.draw.circle(screen, (255, 215, 0), (int(x_screen), int(y)), 10)
            pygame.draw.circle(screen, (255, 240, 150), (int(x_screen), int(y)), 6)

    def check_collect(self, distance_world, player_x_screen, player_y, terrain, collect_radius=18):
        """
        Ramassage par distance (pas de Rect).
        Retourne le nombre d'items ramassés cette frame.
        """
        got = 0
        for it in self.items:
            if it["taken"]:
                continue

            x_screen = player_x_screen + (it["wx"] - distance_world)
            if x_screen < -50 or x_screen > self.width + 50:
                continue

            y_ground = terrain.get_height_screen_x(x_screen)
            y = y_ground - self.y_offset

            dx = x_screen - player_x_screen
            dy = y - player_y
            if dx*dx + dy*dy <= collect_radius*collect_radius:
                it["taken"] = True
                got += 1
        return got