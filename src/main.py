"""
main.py — Tiny Wings (Pygame)

Boucle principale du jeu.
- Terrain infini (sinus) + scrolling piloté par vx.
- Player + collectibles + score.
- 3 causes de Game Over : nuit, chute dans un trou, énergie à 0 trop longtemps.
- Audio : SFX + musique + bouton ON/OFF (touche M).
"""

import pygame
import sys

from terrain import Terrain
from player import Player
from ui import UI
from collectibles import CollectibleManager

pygame.init()

# -------------------------
# AUDIO (SFX + MUSIC) + MUTE
# -------------------------
AUDIO_ENABLED = True
SOUND_COIN = None
SOUND_GAMEOVER = None
MUSIC_PATH = "assets/sounds/music.wav"

try:
    pygame.mixer.init()
    SOUND_COIN = pygame.mixer.Sound("assets/sounds/coin.wav")
    SOUND_GAMEOVER = pygame.mixer.Sound("assets/sounds/gameover.wav")
    pygame.mixer.music.load(MUSIC_PATH)
except Exception:
    AUDIO_ENABLED = False

def set_audio_enabled(enabled: bool) -> None:
    """Active/désactive les sons (SFX + musique)."""
    global AUDIO_ENABLED
    AUDIO_ENABLED = enabled

    if not pygame.mixer.get_init():
        AUDIO_ENABLED = False
        return

    if AUDIO_ENABLED:
        if SOUND_COIN:
            SOUND_COIN.set_volume(0.5)
        if SOUND_GAMEOVER:
            SOUND_GAMEOVER.set_volume(0.6)
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.unpause()
    else:
        if SOUND_COIN:
            SOUND_COIN.set_volume(0.0)
        if SOUND_GAMEOVER:
            SOUND_GAMEOVER.set_volume(0.0)
        pygame.mixer.music.set_volume(0.0)
        pygame.mixer.music.pause()

# volumes init
if pygame.mixer.get_init():
    set_audio_enabled(True)

# -------------------------
# WINDOW
# -------------------------
WIDTH, HEIGHT = 900, 600
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tiny Wings")

# Background image
background = pygame.image.load("assets/images/background.jpg").convert()
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

clock = pygame.time.Clock()

GROUND = (80, 180, 90)
OUTLINE = (20, 90, 40)

ui = UI()

def lerp(a: float, b: float, t: float) -> float:
    """Interpolation linéaire entre a et b (t dans [0,1])."""
    return a + (b - a) * t

def sky_color(dist: float) -> tuple[int, int, int]:
    """Couleur du ciel qui évolue avec la distance."""
    t = min(dist / 50000.0, 1.0)
    r = int(lerp(135, 40, t))
    g = int(lerp(206, 80, t))
    b = int(lerp(235, 140, t))
    return (r, g, b)

def reset_game():
    """Réinitialise une partie (objets + compteurs)."""
    terrain = Terrain(WIDTH, HEIGHT, dx=20)

    bg_terrain = Terrain(WIDTH, HEIGHT, dx=30, base_y_ratio=0.65)
    bg_terrain.waves = [(35, 0.006), (18, 0.012)]

    player = Player(x_screen=250, radius=12)

    collectibles = CollectibleManager(WIDTH, HEIGHT, dx_world=500, y_offset=45)
    coins = 0

    distance = 0.0
    score = 0.0
    night_world_x = -100.0  # pour screencast: nuit tôt
    energy_zero_time = 0.0

    game_over = False
    final_score = 0.0
    game_over_time = 0.0
    new_record = False
    death_reason = ""

    # musique: relancer si audio ON
    if pygame.mixer.get_init() and AUDIO_ENABLED:
        pygame.mixer.music.play(-1)

    return (
        terrain, bg_terrain, player, collectibles, coins,
        distance, score, night_world_x, energy_zero_time,
        game_over, final_score, game_over_time, new_record, death_reason
    )

(
    terrain, bg_terrain, player, collectibles, coins,
    distance, score, night_world_x, energy_zero_time,
    game_over, final_score, game_over_time, new_record, death_reason
) = reset_game()

running = True
phase = 0

while running:
    dt = clock.tick(FPS) / 1000.0

    # -------- EVENTS --------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Toggle audio ON/OFF (M)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
            set_audio_enabled(not AUDIO_ENABLED)

        # touches actives uniquement en Game Over
        if game_over and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_r:
                (
                    terrain, bg_terrain, player, collectibles, coins,
                    distance, score, night_world_x, energy_zero_time,
                    game_over, final_score, game_over_time, new_record, death_reason
                ) = reset_game()

    # -------- UPDATE --------
    if not game_over:
        distance += player.vx * dt

        mult = 2.0 if player.air_time >= 2.0 else 1.0
        score += (player.vx * dt) * mult

        # niveaux
        if distance < 12000:
            phase = 0
        elif distance < 30000:
            phase = 1
        else:
            phase = 2

        if phase == 0:
            terrain.gaps_enabled = False
            terrain.gap_every = 999999.0
            terrain.gap_width = 0.0
            terrain.gap_ramp = 240.0
            night_k, night_b = 0.80, 50.0
            biome_t = 0.0

        elif phase == 1:
            terrain.gaps_enabled = True
            terrain.gap_every = 2200.0
            terrain.gap_width = 100.0
            terrain.gap_ramp = 260.0
            if terrain.next_gap_wx < distance or terrain.next_gap_wx > distance + 1500:
                terrain.next_gap_wx = distance + 900
            night_k, night_b = 0.90, 70.0
            biome_t = min((distance - 6000) / 20000.0, 1.0) * 0.6

        else:
            terrain.gaps_enabled = True
            terrain.gap_every = 900.0
            terrain.gap_width = 320.0
            terrain.gap_ramp = 160.0
            if terrain.next_gap_wx < distance or terrain.next_gap_wx > distance + 900:
                terrain.next_gap_wx = distance + 500
            night_k, night_b = 1.00, 100.0
            biome_t = min((distance - 20000) / 60000.0, 1.0)

        terrain.set_biome(biome_t)

        night_world_x += (player.vx * night_k + night_b) * dt

        bg_terrain.update_scroll(player.vx * dt * 0.5)
        terrain.update_scroll(player.vx * dt)

        player.update(dt, terrain)

        collectibles.update(distance, player.x, terrain)
        got = collectibles.check_collect(distance, player.x, player.y, terrain)
        if got > 0:
            coins += got
            if AUDIO_ENABLED and SOUND_COIN:
                SOUND_COIN.play()

        # GAME OVER 1 : nuit
        if night_world_x >= distance:
            game_over = True
            death_reason = "night"

        # GAME OVER 2 : chute
        if (not game_over) and (player.y > HEIGHT + 200):
            game_over = True
            death_reason = "hole"

        # GAME OVER 3 : énergie = 0 trop longtemps
        if player.energy <= 0.01:
            energy_zero_time += dt
        else:
            energy_zero_time = 0.0

        if (not game_over) and (energy_zero_time > 6.0):
            game_over = True
            death_reason = "energy"

        if game_over:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
            if AUDIO_ENABLED and SOUND_GAMEOVER:
                SOUND_GAMEOVER.play()

            final_score = score
            game_over_time = 0.0
            new_record = ui.update_highscore_if_needed(final_score)

    # -------- DRAW --------
    screen.blit(background, (0, 0))

    bg_terrain.draw(screen, color_ground=(60, 120, 90), color_outline=None)
    terrain.draw(screen, GROUND, OUTLINE)

    player.draw(screen)
    collectibles.draw(screen, distance, player.x, terrain)

    # nuit bande gauche
    night_screen_x = player.x - (distance - night_world_x)
    if night_screen_x > 0:
        w = int(min(night_screen_x, WIDTH))
        overlay = pygame.Surface((w, HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 10, 30, 120))
        screen.blit(overlay, (0, 0))

    # HUD
    ui.draw_hud(screen, score, player.vx, player.state, player.boosting)

    coins_txt = ui.font.render(f"Coins: {coins}", True, (10, 10, 10))
    screen.blit(coins_txt, (12, 40))

    level_txt = ui.font.render(f"Level: {phase+1}", True, (10, 10, 10))
    screen.blit(level_txt, (12, 95))

    # Game over screen + cause
    if game_over:
        game_over_time += dt
        ui.draw_game_over_screen(screen, final_score, game_over_time, is_new_record=new_record)

        reason_map = {
            "night": "Night caught you",
            "hole": "Fell in a hole",
            "energy": "Out of energy",
        }
        reason = reason_map.get(death_reason, "Cause: Unknown")
        reason_surf = ui.font.render(reason, True, (230, 230, 230))
        screen.blit(reason_surf, (WIDTH // 2 - reason_surf.get_width() // 2, HEIGHT // 2 + 150))

    pygame.display.flip()

# clean exit
if pygame.mixer.get_init():
    pygame.mixer.music.stop()
pygame.quit()
sys.exit()