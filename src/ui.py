import pygame
import math
import os
import sys

# Web detection (pygbag / emscripten)
IS_WEB = (sys.platform == "emscripten")

# LocalStorage helpers (web) / file helpers (desktop)
def load_highscore_storage(default: int = 0) -> int:
    """Charge le highscore : localStorage (web) ou fichier (desktop)."""
    if IS_WEB:
        try:
            from platform import window  # type: ignore
            v = window.localStorage.getItem("tiny_wings_highscore")
            return int(v) if v is not None else default
        except Exception:
            return default
    else:
        try:
            if not os.path.exists("highscore.txt"):
                return default
            with open("highscore.txt", "r", encoding="utf-8") as f:
                return int(f.read().strip() or 0)
        except Exception:
            return default


def save_highscore_storage(value: int) -> None:
    """Sauvegarde le highscore : localStorage (web) ou fichier (desktop)."""
    value = int(value)
    if IS_WEB:
        try:
            from platform import window  # type: ignore
            window.localStorage.setItem("tiny_wings_highscore", str(value))
        except Exception:
            pass
    else:
        try:
            with open("highscore.txt", "w", encoding="utf-8") as f:
                f.write(str(value))
        except Exception:
            pass


class UI:
    """Affichage HUD : score + game over + highscore (par utilisateur en web)."""

    def __init__(self):
        pygame.font.init()
        self.font = pygame.font.Font(None, 32)
        self.font_big = pygame.font.Font(None, 72)
        self.font_med = pygame.font.Font(None, 44)

        # Highscore : localStorage en web, fichier en desktop
        self.highscore = load_highscore_storage(0)

    def draw_hud(self, screen, score, vx, state, dive):
        txt = f"Score: {int(score)}"
        surf = self.font.render(txt, True, (10, 10, 10))
        screen.blit(surf, (12, 10))

    def draw_game_over(self, screen):
        surf = self.font_big.render("GAME OVER", True, (240, 240, 240))
        rect = surf.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
        screen.blit(surf, rect)

    def update_highscore_if_needed(self, score: float) -> bool:
        """
        Met à jour highscore si score > highscore.
        Web : sauvegarde dans localStorage (par navigateur).
        Desktop : sauvegarde dans highscore.txt.
        """
        s = int(score)
        if s > int(self.highscore):
            self.highscore = s
            save_highscore_storage(self.highscore)
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