import pygame
import math
import os

class UI:
    """Affichage HUD simple : score + messages."""

    def __init__(self):
        pygame.font.init()
        self.font = pygame.font.Font(None, 32)
        self.font_big = pygame.font.Font(None, 72)
        self.font_med = pygame.font.Font(None, 44)
        self.highscore_path = "highscore.txt"
        self.highscore = self.load_highscore()
    
    def load_highscore(self) -> float:
        """Lit le high score depuis un fichier. Renvoie 0 si absent/illisible."""
        try:
            if not os.path.exists(self.highscore_path):
                return 0.0
            with open(self.highscore_path, "r", encoding="utf-8") as f:
                return float(f.read().strip() or 0)
        except Exception:
            return 0.0

    def draw_hud(self, screen, score, vx, state, dive):
        txt = f"Score: {int(score)}"
        surf = self.font.render(txt, True, (10, 10, 10))
        screen.blit(surf, (12, 10))

    def draw_game_over(self, screen):
        surf = self.font_big.render("GAME OVER", True, (240, 240, 240))
        rect = surf.get_rect(center=(screen.get_width()//2, screen.get_height()//2))
        screen.blit(surf, rect)
    
    def save_highscore(self, score: float):
        """Sauvegarde le high score dans un fichier."""
        with open(self.highscore_path, "w", encoding="utf-8") as f:
            f.write(str(int(score)))
    
    def update_highscore_if_needed(self, score: float) -> bool:
        """Met à jour highscore si score > highscore. Renvoie True si nouveau record."""
        if score > self.highscore:
            self.highscore = score
            self.save_highscore(score)
            return True
        return False

    def draw_game_over_screen(self, screen, score, t, is_new_record=False):
        w, h = screen.get_width(), screen.get_height()

        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((10, 10, 30, 200))
        screen.blit(overlay, (0, 0))

        title = self.font_big.render("GAME OVER", True, (240, 240, 240))
        screen.blit(title, title.get_rect(center=(w // 2, h // 2 - 120)))

        pulse = 1.0 + 0.06 * math.sin(6.0 * t)
        score_txt = f"SCORE: {int(score)}"
        score_surf = self.font_big.render(score_txt, True, (255, 255, 255))
        score_surf = pygame.transform.smoothscale(
            score_surf,
            (int(score_surf.get_width() * pulse), int(score_surf.get_height() * pulse))
        )
        screen.blit(score_surf, score_surf.get_rect(center=(w // 2, h // 2 - 20)))

        hs_txt = f"HIGHSCORE: {int(self.highscore)}"
        hs_color = (255, 230, 140) if is_new_record else (220, 220, 220)
        hs_surf = self.font_med.render(hs_txt, True, hs_color)
        screen.blit(hs_surf, hs_surf.get_rect(center=(w // 2, h // 2 + 45)))

        if is_new_record:
            badge = self.font.render("NEW RECORD!", True, (255, 230, 140))
            screen.blit(badge, badge.get_rect(center=(w // 2, h // 2 + 80)))

        hint = self.font.render("R : Rejouer   |   ESC : Quitter", True, (230, 230, 230))
        screen.blit(hint, hint.get_rect(center=(w // 2, h // 2 + 130)))

    