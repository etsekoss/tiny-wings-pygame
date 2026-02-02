"""
main.py — Tiny Wings (Pygame)

Boucle principale du jeu.
- Terrain infini (sinus) + scrolling piloté par vx.
- Player + collectibles + score.
- 3 causes de Game Over : nuit, chute dans un trou, énergie à 0 trop longtemps.
- Audio : SFX + musique + bouton ON/OFF (touche M).
- Web (pygbag) :
  - musique jouée via pygame.mixer.Sound (plus fiable que mixer.music en Web),
  - démarre après interaction utilisateur,
  - boucle async + await asyncio.sleep(0) pour éviter "Page ne répond pas".
- Difficulté :
  - Level 1 : terrain lisse, pas de trous
  - Level 2 : terrain plus nerveux, quelques trous (max 4)
  - Level 3 : terrain + trous deviennent plus durs progressivement avec la distance
- Mobile :
  - tap/hold écran = même action que ESPACE (pas de clavier virtuel)
"""

import pygame
import sys
import asyncio

from terrain import Terrain
from player import Player
from ui import UI
from collectibles import CollectibleManager

pygame.init()

IS_WEB = (sys.platform == "emscripten")

# -------------------------
# AUDIO (SFX + MUSIC as Sound) + MUTE
# -------------------------
AUDIO_ENABLED = True
SOUND_COIN = None
SOUND_GAMEOVER = None

MUSIC = None
music_channel = None
music_started = False
user_interacted = False

try:
    pygame.mixer.init()
    SOUND_COIN = pygame.mixer.Sound("assets/sounds/coin.wav")
    SOUND_GAMEOVER = pygame.mixer.Sound("assets/sounds/gameover.wav")
    MUSIC = pygame.mixer.Sound("assets/sounds/music_web.wav")
except Exception:
    AUDIO_ENABLED = False


def set_audio_enabled(enabled: bool) -> None:
    """ON/OFF son (web-safe) : volumes uniquement."""
    global AUDIO_ENABLED
    AUDIO_ENABLED = enabled

    if not pygame.mixer.get_init():
        AUDIO_ENABLED = False
        return

    if SOUND_COIN:
        SOUND_COIN.set_volume(0.5 if AUDIO_ENABLED else 0.0)
    if SOUND_GAMEOVER:
        SOUND_GAMEOVER.set_volume(0.6 if AUDIO_ENABLED else 0.0)
    if MUSIC:
        MUSIC.set_volume(0.4 if AUDIO_ENABLED else 0.0)


def try_start_music() -> None:
    """Démarre la musique en boucle après interaction (web policy)."""
    global music_started, music_channel
    if music_started or MUSIC is None:
        return
    if not pygame.mixer.get_init():
        return
    try:
        MUSIC.set_volume(0.4 if AUDIO_ENABLED else 0.0)
        music_channel = MUSIC.play(loops=-1)
        music_started = True
    except pygame.error:
        pass


if pygame.mixer.get_init():
    set_audio_enabled(True)

# -------------------------
# WINDOW
# -------------------------
WIDTH, HEIGHT = 900, 600
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tiny Wings")

background = pygame.image.load("assets/images/background.jpg").convert()
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

clock = pygame.time.Clock()

GROUND = (70, 190, 110)
OUTLINE = (10, 60, 25)

ui = UI()

# -------------------------
# INPUT ABSTRACTION (Desktop + Mobile)
# -------------------------
ACTION_DOWN = False       # état (hold)
ACTION_PRESSED = False    # edge (tap)


def action_down() -> None:
    """Action principale ON (equiv. ESPACE down / touch down)."""
    global ACTION_DOWN, ACTION_PRESSED
    if not ACTION_DOWN:
        ACTION_PRESSED = True
    ACTION_DOWN = True


def action_up() -> None:
    """Action principale OFF (equiv. ESPACE up / touch up)."""
    global ACTION_DOWN
    ACTION_DOWN = False


def reset_game():
    """Réinitialise une partie (objets + compteurs)."""
    terrain = Terrain(WIDTH, HEIGHT, dx=14, base_y_ratio=0.65)

    bg_terrain = Terrain(WIDTH, HEIGHT, dx=30, base_y_ratio=0.65)
    bg_terrain.waves = [(35, 0.006), (18, 0.012)]

    player = Player(x_screen=250, radius=12)

    collectibles = CollectibleManager(WIDTH, HEIGHT, dx_world=500, y_offset=45)
    coins = 0

    distance = 0.0
    score = 0.0
    night_world_x = -1200.0
    energy_zero_time = 0.0

    game_over = False
    final_score = 0.0
    game_over_time = 0.0
    new_record = False
    death_reason = ""

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
prev_phase = 0


async def run():
    global running, phase, prev_phase
    global terrain, bg_terrain, player, collectibles, coins
    global distance, score, night_world_x, energy_zero_time
    global game_over, final_score, game_over_time, new_record, death_reason
    global AUDIO_ENABLED, music_started, user_interacted, music_channel
    global ACTION_DOWN, ACTION_PRESSED

    while running:
        dt = clock.tick(FPS) / 1000.0

        # reset edge chaque frame
        ACTION_PRESSED = False

        # -------- EVENTS --------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # WebAudio: 1ère interaction
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                user_interacted = True
                if not music_started:
                    try_start_music()

            # Toggle audio ON/OFF (M)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                set_audio_enabled(not AUDIO_ENABLED)
                if user_interacted and (not music_started):
                    try_start_music()

            # ---- ACTION INPUT ----
            # Desktop: SPACE
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                action_down()
            if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                action_up()

            # Mobile/Web: touch souvent via souris
            if event.type == pygame.MOUSEBUTTONDOWN:
                action_down()
            if event.type == pygame.MOUSEBUTTONUP:
                action_up()

            # Touch events (si disponibles selon build pygame)
            if hasattr(pygame, "FINGERDOWN") and event.type == pygame.FINGERDOWN:
                action_down()
            if hasattr(pygame, "FINGERUP") and event.type == pygame.FINGERUP:
                action_up()

            # GAME OVER inputs
            if game_over and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    (
                        terrain, bg_terrain, player, collectibles, coins,
                        distance, score, night_world_x, energy_zero_time,
                        game_over, final_score, game_over_time, new_record, death_reason
                    ) = reset_game()

                    # reset musique (redémarre après interaction)
                    if music_channel:
                        try:
                            music_channel.stop()
                        except Exception:
                            pass
                    music_channel = None
                    music_started = False
                    user_interacted = False

                    prev_phase = 0
                    phase = 0
                    ACTION_DOWN = False
                    ACTION_PRESSED = False

        # retry auto musique si interaction déjà faite
        if user_interacted and (not music_started):
            try_start_music()

        # -------- UPDATE --------
        if not game_over:
            distance += player.vx * dt

            mult = 2.0 if player.air_time >= 2.0 else 1.0
            score += (player.vx * dt) * mult

            prev_phase = phase
            if distance < 12000:
                phase = 0
            elif distance < 30000:
                phase = 1
            else:
                phase = 2

            # changement de niveau -> reset trous
            if phase != prev_phase:
                terrain.gaps = []
                terrain.next_gap_wx = distance + 900

            # ---- difficulté / paramètres ----
            if phase == 0:
                terrain.gaps_enabled = False
                terrain.gaps = []
                terrain.set_waves([(55, 0.008), (25, 0.016), (10, 0.030)])
                night_k, night_b = 0.80, 40.0

            elif phase == 1:
                terrain.gaps_enabled = True
                terrain.set_waves([(70, 0.010), (35, 0.020), (15, 0.040)])
                terrain.gap_every = 5000.0
                terrain.gap_width = 90.0
                terrain.gap_ramp = 260.0
                if len(terrain.gaps) >= 4:
                    terrain.gaps_enabled = False
                night_k, night_b = 0.90, 60.0

            else:
                t3 = min(max((distance - 30000.0) / 60000.0, 0.0), 1.0)

                waves_easy = [(75, 0.010), (38, 0.022), (18, 0.045)]
                waves_hard = [(95, 0.016), (55, 0.035), (28, 0.070)]
                terrain.set_waves([
                    (waves_easy[i][0] + (waves_hard[i][0] - waves_easy[i][0]) * t3,
                     waves_easy[i][1] + (waves_hard[i][1] - waves_easy[i][1]) * t3)
                    for i in range(3)
                ])

                terrain.gaps_enabled = True
                terrain.gap_every = 1800.0 - 900.0 * t3
                terrain.gap_width = 140.0 + 140.0 * t3
                terrain.gap_ramp = 240.0 - 80.0 * t3

                night_k, night_b = 1.00, 100.0

            # ---- nuit + scrolling ----
            night_world_x += (player.vx * night_k + night_b) * dt

            bg_terrain.update_scroll(player.vx * dt * 0.5)
            terrain.update_scroll(player.vx * dt)

            # ---- player input injection ----
            player.boosting = ACTION_DOWN
            player.action_pressed = ACTION_PRESSED
            player.update(dt, terrain)

            # collectibles
            collectibles.update(distance, player.x, terrain)
            got = collectibles.check_collect(distance, player.x, player.y, terrain)
            if got > 0:
                coins += got
                if AUDIO_ENABLED and SOUND_COIN:
                    SOUND_COIN.play()

            # ---- game over ----
            if night_world_x >= distance:
                game_over = True
                death_reason = "night"

            if (not game_over) and (player.y > HEIGHT + 200):
                game_over = True
                death_reason = "hole"

            if player.energy <= 0.01:
                energy_zero_time += dt
            else:
                energy_zero_time = 0.0

            if (not game_over) and (energy_zero_time > 6.0):
                game_over = True
                death_reason = "energy"

            if game_over:
                if music_channel:
                    try:
                        music_channel.stop()
                    except Exception:
                        pass
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

        night_screen_x = player.x - (distance - night_world_x)
        if night_screen_x > 0:
            w = int(min(night_screen_x, WIDTH))
            overlay = pygame.Surface((w, HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 10, 30, 120))
            screen.blit(overlay, (0, 0))

        ui.draw_hud(screen, score, player.vx, player.state, player.boosting)

        coins_txt = ui.font.render(f"Coins: {coins}", True, (10, 10, 10))
        screen.blit(coins_txt, (12, 40))

        level_txt = ui.font.render(f"Level: {phase+1}", True, (10, 10, 10))
        screen.blit(level_txt, (12, 95))

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
        await asyncio.sleep(0)


asyncio.run(run())

pygame.quit()
if not IS_WEB:
    sys.exit()