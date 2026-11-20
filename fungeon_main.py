"""Arcade views and the main gameplay loop for FUNgeon."""

import math

import arcade

from fungeon_UI import FungeonUI
from fungeon_enemies import Boss, create_enemy
from fungeon_loot import (
    CHEST_HEIGHT,
    ITEMS,
    LOOT_ITEM_RADIUS,
    Chest,
    WEAPONS,
    spawn_loot,
)
from fungeon_level import Level, load_level, next_level_path
from fungeon_obstacles import BlockGrid


SCREEN_TITLE = "FUNgeon"

BACKGROUND = (24, 28, 42)
PANEL = (48, 56, 78)
ACCENT = (100, 220, 170)
TEXT = (240, 244, 255)
PLAYER_COLOR = (255, 190, 80)
PLAYER_SPEED = 260
CHEST_INTERACTION_RANGE = 90
LOOT_PICKUP_RANGE = 52
SLASH_DURATION = 0.24
DOOR_WIDTH = 110
DOOR_HEIGHT = 14
STATUS_FADE_START = 2.0
STATUS_FADE_END = 3.0
MAX_STATUS_MESSAGES = 5
STATUS_MESSAGE_LINE_HEIGHT = 24
BOMB_FUSE = 1.0
CHAIN_EFFECT_DURATION = 0.45
EXPLOSION_EFFECT_DURATION = 0.28


class TimedBomb:
    """A dropped bomb with a visible blast radius and a one-second fuse."""

    def __init__(self, x, y, radius, damage):
        self.center_x = x
        self.center_y = y
        self.radius = radius
        self.damage = damage
        self.fuse_remaining = BOMB_FUSE

    def update(self, delta_time):
        self.fuse_remaining -= delta_time
        return self.fuse_remaining <= 0

    def draw(self):
        arcade.draw_circle_filled(
            self.center_x,
            self.center_y,
            7,
            (35, 38, 48),
        )
        arcade.draw_circle_outline(
            self.center_x,
            self.center_y,
            7,
            (255, 125, 70),
            border_width=2,
        )
        # Show the exact damage area while the bomb is armed.
        arcade.draw_circle_filled(
            self.center_x,
            self.center_y,
            self.radius,
            (255, 90, 45, 28),
        )
        arcade.draw_circle_outline(
            self.center_x,
            self.center_y,
            self.radius,
            (255, 135, 75, 190),
            border_width=3,
        )


class ExplosionEffect:
    """Brief expanding-looking ring marking where a bomb detonated."""

    def __init__(self, x, y, radius):
        self.center_x = x
        self.center_y = y
        self.radius = radius
        self.remaining = EXPLOSION_EFFECT_DURATION

    def draw(self):
        arcade.draw_circle_outline(
            self.center_x,
            self.center_y,
            self.radius,
            (255, 205, 95, 220),
            border_width=5,
        )


class MenuView(arcade.View):
    """Start screen that keeps the selected level for the new run."""

    def __init__(self, level: Level | None = None):
        super().__init__()
        self.level = level if level is not None else load_level()

    def on_show_view(self):
        self.window.background_color = BACKGROUND

    def on_draw(self):
        self.clear()
        center_x = self.window.width / 2
        center_y = self.window.height / 2

        arcade.draw_text(
            "FUNgeon",
            center_x,
            center_y + 100,
            TEXT,
            font_size=54,
            bold=True,
            anchor_x="center",
        )
        arcade.draw_rect_filled(
            arcade.XYWH(center_x, center_y - 10, 220, 64),
            PANEL,
        )
        arcade.draw_text(
            "START GAME",
            center_x,
            center_y - 18,
            ACCENT,
            font_size=22,
            bold=True,
            anchor_x="center",
        )
        arcade.draw_text(
            "Press ENTER or click to play",
            center_x,
            center_y - 85,
            TEXT,
            font_size=16,
            anchor_x="center",
        )

    def start_game(self):
        self.window.show_view(GameView(self.level))

    def on_key_press(self, key, modifiers):
        if key in (arcade.key.ENTER, arcade.key.SPACE):
            self.start_game()

    def on_mouse_press(self, x, y, button, modifiers):
        center_x = self.window.width / 2
        center_y = self.window.height / 2
        inside_button = (
            center_x - 110 <= x <= center_x + 110
            and center_y - 42 <= y <= center_y + 22
        )
        if button == arcade.MOUSE_BUTTON_LEFT and inside_button:
            self.start_game()


class GameOverView(arcade.View):
    """End screen with restart and return-to-menu controls."""

    def __init__(self, level: Level):
        super().__init__()
        self.level = level

    def on_show_view(self):
        self.window.background_color = BACKGROUND

    def on_draw(self):
        self.clear()
        center_x = self.window.width / 2
        center_y = self.window.height / 2
        arcade.draw_text(
            "GAME OVER",
            center_x,
            center_y + 55,
            (240, 95, 105),
            font_size=48,
            bold=True,
            anchor_x="center",
        )
        arcade.draw_text(
            "Press ENTER to try again",
            center_x,
            center_y - 10,
            TEXT,
            font_size=20,
            anchor_x="center",
        )
        arcade.draw_text(
            "Press ESC to return to the menu",
            center_x,
            center_y - 50,
            TEXT,
            font_size=16,
            anchor_x="center",
        )

    def on_key_press(self, key, modifiers):
        if key in (arcade.key.ENTER, arcade.key.SPACE):
            self.window.show_view(GameView(load_level()))
        elif key == arcade.key.ESCAPE:
            self.window.show_view(MenuView(self.level))


class GameView(arcade.View):
    """Owns the current room state and connects input, game logic, and drawing."""

    def __init__(self, level: Level | None = None):
        super().__init__()
        self.level = level if level is not None else load_level()
        # Instantiate room entities from the parsed level spawn records.
        self.block_grid = BlockGrid(
            self.level.width,
            self.level.height,
            self.level.blocks,
        )
        self.player_x, self.player_y = self.level.player_start
        self.held_keys = set()
        self.chests = [Chest(x, y) for x, y in self.level.chests]
        self.ground_items = []
        self.status_messages: list[tuple[str, float]] = []
        self.health = 100
        self.max_health = 100
        self.shield = 0
        self.damage_boost = 0
        self.damage_boost_timer = 0
        self.active_bombs: list[TimedBomb] = []
        self.explosion_effects: list[ExplosionEffect] = []
        self.chain_lightning_effects: list[
            tuple[float, float, float, float, float]
        ] = []
        self.score = 0
        self.ui = FungeonUI()
        self.inventory: dict[str, tuple[int, str]] = {
            "training sword": (
                1,
                WEAPONS["training sword"]["rarity"],
            )
        }
        self.inventory_open = False
        self.inventory_menu_item = None
        self.slot_items: dict[int, str] = {1: "training sword"}
        self.enemies = [
            create_enemy(enemy_type, x, y)
            for enemy_type, x, y in self.level.enemies
        ]
        self.slash_angle = 0
        self.slash_elapsed = SLASH_DURATION
        self.slash_type = "slash"
        self.slash_width = 0
        self.slash_arc_angle = 76
        self.attack_cooldown_remaining = 0
        self.slash_range = WEAPONS["training sword"]["range"]

    def on_show_view(self):
        self.window.background_color = BACKGROUND

    def on_draw(self):
        # Draw the room and entities first, then HUD prompts and overlays.
        self.clear()
        self.block_grid.draw()
        arcade.draw_rect_filled(
            arcade.XYWH(self.window.width / 2, 36, self.window.width, 72),
            PANEL,
        )
        arcade.draw_text(
            "Move: WASD / arrows   Menu: ESC",
            20,
            24,
            TEXT,
            font_size=16,
        )
        arcade.draw_text(
            f"Score: {self.score}",
            20,
            self.window.height - 32,
            TEXT,
            font_size=18,
            bold=True,
        )
        for chest in self.chests:
            chest.draw()
        for item in self.ground_items:
            item.draw()
        for enemy in self.enemies:
            enemy.draw()
        for bomb in self.active_bombs:
            bomb.draw()
        for effect in self.explosion_effects:
            effect.draw()
        self.draw_chain_lightning()
        for boss in self.enemies:
            if isinstance(boss, Boss) and boss.is_alive:
                boss.draw_health_bar(self.window.width, self.window.height)
        if self.room_is_cleared:
            self.draw_exit_door()
        arcade.draw_circle_filled(self.player_x, self.player_y, 22, PLAYER_COLOR)
        arcade.draw_circle_filled(self.player_x, self.player_y, 8, ACCENT)
        self.draw_slash()
        self.ui.draw(
            self.window.width,
            self.window.height,
            self.health,
            self.max_health,
            self.inventory,
            self.slot_items,
        )
        self.ui.draw_active_effects(
            self.window.width,
            self.shield,
            self.damage_boost,
            self.damage_boost_timer,
        )

        nearest_item = self.closest_loot_in_range()
        if nearest_item is not None:
            arcade.draw_text(
                f"Press E to pick up {nearest_item.item}",
                nearest_item.center_x,
                nearest_item.center_y + LOOT_ITEM_RADIUS + 10,
                ACCENT,
                font_size=16,
                bold=True,
                anchor_x="center",
            )
        else:
            nearby_chest = self.closest_chest_in_range()
            if nearby_chest is not None and not nearby_chest.is_open:
                arcade.draw_text(
                    f"Press E to open {nearby_chest.rarity} chest",
                    nearby_chest.center_x,
                    nearby_chest.center_y + CHEST_HEIGHT + 22,
                    TEXT,
                    font_size=16,
                    bold=True,
                    anchor_x="center",
                )
        for index, (message, elapsed) in enumerate(self.status_messages):
            if elapsed <= STATUS_FADE_START:
                status_alpha = 255
            else:
                fade_progress = (
                    (elapsed - STATUS_FADE_START)
                    / (STATUS_FADE_END - STATUS_FADE_START)
                )
                status_alpha = round(255 * (1 - fade_progress))
            arcade.draw_text(
                message,
                self.window.width / 2,
                96
                + (len(self.status_messages) - 1 - index)
                * STATUS_MESSAGE_LINE_HEIGHT,
                (*ACCENT, status_alpha),
                font_size=16,
                anchor_x="center",
            )
        if self.room_is_cleared and self.is_player_at_exit:
            arcade.draw_text(
                "Entering next room...",
                self.window.width / 2,
                self.window.height - 105,
                ACCENT,
                font_size=16,
                bold=True,
                anchor_x="center",
            )
        if self.inventory_open:
            self.ui.draw_inventory(
                self.window.width,
                self.window.height,
                self.inventory,
                self.slot_items,
                self.inventory_menu_item,
            )

    def closest_chest_in_range(self):
        """Find the nearest chest the player can currently interact with."""
        # Track the winner in one pass instead of allocating and rescanning a list.
        nearest_chest = None
        interaction_range_squared = CHEST_INTERACTION_RANGE**2
        nearest_distance_squared = interaction_range_squared
        for chest in self.chests:
            distance_squared = (
                (self.player_x - chest.center_x) ** 2
                + (self.player_y - chest.center_y) ** 2
            )
            if distance_squared <= interaction_range_squared and (
                nearest_chest is None
                or distance_squared < nearest_distance_squared
            ):
                nearest_chest = chest
                nearest_distance_squared = distance_squared
        return nearest_chest

    @property
    def room_is_cleared(self):
        # An empty enemy list also counts as a cleared room.
        return all(not enemy.is_alive for enemy in self.enemies)

    @property
    def is_player_at_exit(self):
        return (
            abs(self.player_x - self.window.width / 2)
            <= DOOR_WIDTH / 2 + 22
            and self.player_y >= self.window.height - DOOR_HEIGHT - 22
        )

    def draw_exit_door(self):
        door_center_x = self.window.width / 2
        door_center_y = self.window.height - DOOR_HEIGHT / 2
        arcade.draw_rect_filled(
            arcade.XYWH(door_center_x, door_center_y, DOOR_WIDTH, DOOR_HEIGHT),
            (18, 22, 32),
        )
        arcade.draw_rect_outline(
            arcade.XYWH(door_center_x, door_center_y, DOOR_WIDTH, DOOR_HEIGHT),
            ACCENT,
            border_width=3,
        )
        arcade.draw_text(
            "EXIT - WALK INTO THE GLOW",
            door_center_x,
            self.window.height - DOOR_HEIGHT - 24,
            ACCENT,
            font_size=12,
            bold=True,
            anchor_x="center",
        )

    def advance_to_next_room(self):
        # Replace room entities but retain player health, score, and equipment.
        self.level = load_level(next_level_path(self.level.source_path))
        self.block_grid = BlockGrid(
            self.level.width,
            self.level.height,
            self.level.blocks,
        )
        self.player_x, self.player_y = self.level.player_start
        self.chests = [Chest(x, y) for x, y in self.level.chests]
        self.enemies = [
            create_enemy(enemy_type, x, y)
            for enemy_type, x, y in self.level.enemies
        ]
        self.ground_items.clear()
        self.held_keys.clear()
        self.show_status_message("A new room!")
        self.window.set_size(self.level.width, self.level.height)

    def show_status_message(self, message):
        # Keep only recent action feedback; each entry fades independently.
        self.status_messages.append((message, 0.0))
        self.status_messages = self.status_messages[-MAX_STATUS_MESSAGES:]

    def closest_loot_in_range(self):
        """Return only the nearest floor item when it is close enough to pick up."""
        # Combine the range check and nearest-item search into one pass.
        closest_item = None
        pickup_range_squared = LOOT_PICKUP_RANGE**2
        closest_distance_squared = pickup_range_squared
        for item in self.ground_items:
            distance_squared = (
                (self.player_x - item.center_x) ** 2
                + (self.player_y - item.center_y) ** 2
            )
            if distance_squared <= pickup_range_squared and (
                closest_item is None or distance_squared < closest_distance_squared
            ):
                closest_item = item
                closest_distance_squared = distance_squared
        return closest_item

    def damage_player(self, amount):
        remaining_damage = max(0, amount)
        absorbed = min(self.shield, remaining_damage)
        self.shield -= absorbed
        self.health = max(0, self.health - (remaining_damage - absorbed))

    def heal_player(self, amount):
        self.health = min(self.max_health, self.health + max(0, amount))

    def damage_enemy(self, enemy, amount):
        """Apply damage and award kill points consistently for attacks and items."""
        was_alive = enemy.is_alive
        enemy.take_damage(amount)
        if was_alive and not enemy.is_alive:
            self.score += enemy.points

    def use_inventory_item(self, item_name):
        """Consume one utility item and apply its configured effect."""
        if item_name not in ITEMS:
            return False
        if item_name not in self.inventory:
            return False
        amount, _ = self.inventory[item_name]
        item = ITEMS[item_name]
        effect = item["effect"]
        if effect == "heal" and self.health == self.max_health:
            self.show_status_message("Health is already full.")
            return False

        if effect == "heal":
            self.heal_player(item["value"])
        elif effect == "blast":
            self.active_bombs.append(
                TimedBomb(
                    self.player_x,
                    self.player_y,
                    item["radius"],
                    item["value"],
                )
            )
        elif effect == "stun":
            self._stun_enemies_in_radius(item["radius"], item["duration"])
        elif effect == "shield":
            self.shield += item["value"]
        elif effect == "chain":
            targets = sorted(
                (
                    enemy
                    for enemy in self.enemies
                    if enemy.is_alive
                    and math.hypot(
                        enemy.center_x - self.player_x,
                        enemy.center_y - self.player_y,
                    ) <= item["radius"]
                ),
                key=lambda enemy: math.hypot(
                    enemy.center_x - self.player_x,
                    enemy.center_y - self.player_y,
                ),
            )
            for enemy in targets[:3]:
                self.damage_enemy(enemy, item["value"])
                self.chain_lightning_effects.append(
                    (
                        self.player_x,
                        self.player_y,
                        enemy.center_x,
                        enemy.center_y,
                        CHAIN_EFFECT_DURATION,
                    )
                )
        elif effect == "damage_boost":
            self.damage_boost = item["value"] / 100
            self.damage_boost_timer = max(
                self.damage_boost_timer,
                item["duration"],
            )
        elif effect == "frost":
            self._stun_enemies_in_radius(
                item["radius"],
                item["duration"],
                item["value"],
            )
        elif effect == "phoenix":
            self.heal_player(item["value"])
            self.shield += 25
        elif effect == "time_stop":
            self._stun_enemies_in_radius(item["radius"], item["duration"])
        elif effect == "void_blast":
            self.active_bombs.append(
                TimedBomb(
                    self.player_x,
                    self.player_y,
                    item["radius"],
                    item["value"],
                )
            )

        if amount <= 1:
            del self.inventory[item_name]
            self.slot_items = {
                slot: equipped_item
                for slot, equipped_item in self.slot_items.items()
                if equipped_item != item_name
            }
        else:
            self.inventory[item_name] = (amount - 1, self.inventory[item_name][1])
        if effect in ("blast", "void_blast"):
            self.show_status_message(
                f"{item_name.title()} dropped; detonates in one second!"
            )
        else:
            self.show_status_message(f"Used {item_name}.")
        return True

    def draw_chain_lightning(self):
        """Render bright zig-zag links from the player to each struck enemy."""
        for start_x, start_y, end_x, end_y, remaining in self.chain_lightning_effects:
            progress = max(0, min(1, remaining / CHAIN_EFFECT_DURATION))
            alpha = round(255 * progress)
            delta_x = end_x - start_x
            delta_y = end_y - start_y
            length = math.hypot(delta_x, delta_y)
            if length == 0:
                continue
            perpendicular_x = -delta_y / length
            perpendicular_y = delta_x / length
            points = [(start_x, start_y)]
            for index in range(1, 7):
                fraction = index / 7
                offset = 7 if index % 2 else -7
                points.append(
                    (
                        start_x + delta_x * fraction + perpendicular_x * offset,
                        start_y + delta_y * fraction + perpendicular_y * offset,
                    )
                )
            points.append((end_x, end_y))
            for (x1, y1), (x2, y2) in zip(points, points[1:]):
                arcade.draw_line(
                    x1,
                    y1,
                    x2,
                    y2,
                    (55, 190, 255, alpha),
                    line_width=9,
                )
                arcade.draw_line(
                    x1,
                    y1,
                    x2,
                    y2,
                    (230, 250, 255, alpha),
                    line_width=3,
                )

    def update_item_effects(self, delta_time):
        """Advance delayed bomb, explosion, and chain-lightning visuals."""
        # Age existing explosion rings before adding new detonations this frame.
        remaining_explosions = []
        for effect in self.explosion_effects:
            effect.remaining -= delta_time
            if effect.remaining > 0:
                remaining_explosions.append(effect)
        self.explosion_effects = remaining_explosions

        active_bombs = []
        for bomb in self.active_bombs:
            if bomb.update(delta_time):
                self._damage_enemies_in_radius(
                    bomb.radius,
                    bomb.damage,
                    bomb.center_x,
                    bomb.center_y,
                )
                self.explosion_effects.append(
                    ExplosionEffect(bomb.center_x, bomb.center_y, bomb.radius)
                )
            else:
                active_bombs.append(bomb)
        self.active_bombs = active_bombs

        self.chain_lightning_effects = [
            (start_x, start_y, end_x, end_y, remaining - delta_time)
            for start_x, start_y, end_x, end_y, remaining
            in self.chain_lightning_effects
            if remaining - delta_time > 0
        ]

    def _damage_enemies_in_radius(self, radius, damage, center_x=None, center_y=None):
        center_x = self.player_x if center_x is None else center_x
        center_y = self.player_y if center_y is None else center_y
        for enemy in self.enemies:
            if enemy.is_alive and math.hypot(
                enemy.center_x - center_x,
                enemy.center_y - center_y,
            ) <= radius + enemy.size:
                self.damage_enemy(enemy, damage)

    def _stun_enemies_in_radius(self, radius, duration, damage=0):
        for enemy in self.enemies:
            if enemy.is_alive and math.hypot(
                enemy.center_x - self.player_x,
                enemy.center_y - self.player_y,
            ) <= radius + enemy.size:
                if damage:
                    self.damage_enemy(enemy, damage)
                enemy.apply_stun(duration)

    def draw_slash(self):
        if self.slash_elapsed >= SLASH_DURATION:
            return

        # Show a distinct short-lived shape for the equipped weapon's attack.
        progress = self.slash_elapsed / SLASH_DURATION
        direction_x = math.cos(self.slash_angle)
        direction_y = math.sin(self.slash_angle)
        color = (255, 240, 170, 210)

        if self.slash_type == "slash":
            sweep = math.radians(self.slash_arc_angle)
            arc_half_width = math.radians(8)
            arc_center = self.slash_angle - sweep / 2 + sweep * progress
            arcade.draw_arc_outline(
                self.player_x,
                self.player_y,
                self.slash_range * 2,
                self.slash_range * 2,
                color,
                math.degrees(arc_center - arc_half_width),
                math.degrees(arc_center + arc_half_width),
                border_width=8,
            )
        elif self.slash_type == "stab":
            tip_x = self.player_x + direction_x * self.slash_range
            tip_y = self.player_y + direction_y * self.slash_range
            side_x = -direction_y * self.slash_width / 2
            side_y = direction_x * self.slash_width / 2
            arcade.draw_line(
                self.player_x,
                self.player_y,
                tip_x,
                tip_y,
                color,
                line_width=6,
            )
            arcade.draw_line(
                tip_x - side_x,
                tip_y - side_y,
                tip_x + side_x,
                tip_y + side_y,
                color,
                line_width=5,
            )
        elif self.slash_type == "slam":
            side_x = -direction_y * self.slash_width / 2
            side_y = direction_x * self.slash_width / 2
            points = [
                (self.player_x + side_x, self.player_y + side_y),
                (
                    self.player_x + direction_x * self.slash_range + side_x,
                    self.player_y + direction_y * self.slash_range + side_y,
                ),
                (
                    self.player_x + direction_x * self.slash_range - side_x,
                    self.player_y + direction_y * self.slash_range - side_y,
                ),
                (self.player_x - side_x, self.player_y - side_y),
            ]
            arcade.draw_polygon_filled(points, (255, 190, 90, 45))
            arcade.draw_polygon_outline(points, color, line_width=5)
        elif self.slash_type == "spin":
            arcade.draw_circle_outline(
                self.player_x,
                self.player_y,
                self.slash_range,
                color,
                border_width=8,
            )

    def attack(self, mouse_x, mouse_y):
        # The selected slot determines attack stats; empty slots cannot attack.
        weapon_name = self.slot_items.get(self.ui.selected_slot)
        if weapon_name is None or self.attack_cooldown_remaining > 0:
            return

        weapon = WEAPONS[weapon_name]
        # Use the cursor's direction relative to the player as the attack's center.
        self.slash_angle = math.atan2(
            mouse_y - self.player_y,
            mouse_x - self.player_x,
        )
        self.slash_range = weapon["range"]
        self.slash_type = weapon["attack_type"]
        self.slash_width = weapon["width"]
        self.slash_arc_angle = weapon["arc_angle"]
        self.slash_elapsed = 0
        self.attack_cooldown_remaining = weapon["cooldown"]

        # The aim is shared by every enemy hit in this single attack.
        direction_x = math.cos(self.slash_angle)
        direction_y = math.sin(self.slash_angle)
        for enemy in self.enemies:
            if not enemy.is_alive:
                continue

            # Test each weapon against the shape and reach of its attack type.
            offset_x = enemy.center_x - self.player_x
            offset_y = enemy.center_y - self.player_y
            distance = math.hypot(offset_x, offset_y)
            forward_distance = offset_x * direction_x + offset_y * direction_y
            signed_side_distance = offset_x * -direction_y + offset_y * direction_x
            side_distance = abs(signed_side_distance)

            if weapon["attack_type"] == "spin":
                hits = distance <= weapon["range"] + enemy.size
            elif weapon["attack_type"] == "slash":
                enemy_angle = math.atan2(offset_y, offset_x)
                angle_difference = math.atan2(
                    math.sin(enemy_angle - self.slash_angle),
                    math.cos(enemy_angle - self.slash_angle),
                )
                hits = (
                    distance <= weapon["range"] + enemy.size
                    and abs(angle_difference)
                    <= math.radians(weapon["arc_angle"] / 2)
                )
            elif weapon["attack_type"] == "stab":
                hits = (
                    -enemy.size <= forward_distance <= weapon["range"] + enemy.size
                    and side_distance <= weapon["width"] / 2 + enemy.size
                )
            else:
                # Treat the target as a circle against the slam's actual box.
                closest_forward = max(0, min(weapon["range"], forward_distance))
                closest_side = max(
                    -weapon["width"] / 2,
                    min(weapon["width"] / 2, signed_side_distance),
                )
                hits = math.hypot(
                    forward_distance - closest_forward,
                    signed_side_distance - closest_side,
                ) <= enemy.size

            if hits:
                self.damage_enemy(
                    enemy,
                    round(weapon["damage"] * (1 + self.damage_boost)),
                )

    def on_update(self, delta_time):
        # Expire old feedback and pause game simulation while inventory is open.
        self.status_messages = [
            (message, elapsed + delta_time)
            for message, elapsed in self.status_messages
            if elapsed + delta_time < STATUS_FADE_END
        ]
        if self.inventory_open:
            return
        if self.health <= 0:
            self.window.show_view(GameOverView(self.level))
            return
        self.update_item_effects(delta_time)

        if self.room_is_cleared and self.is_player_at_exit:
            self.advance_to_next_room()
            return

        self.slash_elapsed = min(
            SLASH_DURATION,
            self.slash_elapsed + delta_time,
        )
        self.damage_boost_timer = max(0, self.damage_boost_timer - delta_time)
        if self.damage_boost_timer == 0:
            self.damage_boost = 0
        self.attack_cooldown_remaining = max(
            0,
            self.attack_cooldown_remaining - delta_time,
        )
        horizontal = (
            int(arcade.key.RIGHT in self.held_keys or arcade.key.D in self.held_keys)
            - int(arcade.key.LEFT in self.held_keys or arcade.key.A in self.held_keys)
        )
        vertical = (
            int(arcade.key.UP in self.held_keys or arcade.key.W in self.held_keys)
            - int(arcade.key.DOWN in self.held_keys or arcade.key.S in self.held_keys)
        )

        length = math.hypot(horizontal, vertical)
        if length:
            # Normalize diagonal movement so it is not faster than straight movement.
            movement_x = horizontal / length * PLAYER_SPEED * delta_time
            movement_y = vertical / length * PLAYER_SPEED * delta_time
            if self.block_grid.blocked_cells:
                self.player_x, self.player_y = self.block_grid.move_circle(
                    self.player_x,
                    self.player_y,
                    movement_x,
                    movement_y,
                    22,
                )
            else:
                self.player_x += movement_x
                self.player_y += movement_y

        # Keep the player within the room, clear of the HUD strip.
        self.player_x = max(22, min(self.window.width - 22, self.player_x))
        self.player_y = max(58, min(self.window.height - 22, self.player_y))

        for enemy in self.enemies:
            # Enemy.update returns damage only when an attack cooldown completes.
            incoming_damage = enemy.update(
                self.player_x,
                self.player_y,
                delta_time,
                self.block_grid,
            )
            if incoming_damage:
                self.damage_player(incoming_damage)

        if self.health <= 0:
            self.window.show_view(GameOverView(self.level))

    def on_key_press(self, key, modifiers):
        # Inventory input takes priority so gameplay controls do not fire behind it.
        if key == arcade.key.TAB:
            self.inventory_open = not self.inventory_open
            self.inventory_menu_item = None
        elif self.inventory_open and key == arcade.key.ESCAPE:
            self.window.show_view(MenuView(self.level))
        elif self.inventory_open:
            return
        elif key == arcade.key.ESCAPE:
            self.window.show_view(MenuView(self.level))
        elif key == arcade.key.KEY_1:
            self.ui.select_slot(1)
        elif key == arcade.key.KEY_2:
            self.ui.select_slot(2)
        elif key == arcade.key.F:
            self.chests.append(Chest(self.player_x, self.player_y))
            self.show_status_message("Chest spawned!")
        elif key == arcade.key.E:
            # Prefer nearby floor loot; otherwise open the closest unopened chest.
            nearest_item = self.closest_loot_in_range()
            if nearest_item is not None:
                self.ground_items.remove(nearest_item)
                previous_amount, rarity = self.inventory.get(
                    nearest_item.item,
                    (0, nearest_item.rarity),
                )
                self.inventory[nearest_item.item] = (
                    previous_amount + nearest_item.amount,
                    rarity,
                )
                self.show_status_message(
                    f"Picked up {nearest_item.amount} {nearest_item.item} "
                    f"({nearest_item.rarity})"
                )
            else:
                nearby_chest = self.closest_chest_in_range()
                if nearby_chest is not None and not nearby_chest.is_open:
                    loot = nearby_chest.open()
                    self.ground_items.extend(
                        spawn_loot(
                            nearby_chest.center_x,
                            nearby_chest.center_y,
                            loot,
                        )
                    )
                    if loot:
                        item_count = sum(
                            drop["quantity"] for drop in loot.values()
                        )
                        self.show_status_message(
                            f"{nearby_chest.rarity.title()} chest dropped "
                            f"{item_count} item(s)!"
                        )
                    else:
                        self.show_status_message("The chest was empty.")
        else:
            self.held_keys.add(key)

    def on_key_release(self, key, modifiers):
        self.held_keys.discard(key)

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        if self.inventory_open:
            # A click either chooses a dropdown action or selects another item.
            slot = self.ui.inventory_menu_option_at(
                x,
                y,
                self.window.width,
                self.window.height,
                self.inventory,
                self.inventory_menu_item,
            )
            if slot is not None and self.inventory_menu_item is not None:
                item_name = self.inventory_menu_item
                current_slot = next(
                    (
                        equipped_slot
                        for equipped_slot, equipped_item in self.slot_items.items()
                        if equipped_item == item_name
                    ),
                    None,
                )
                if current_slot == slot:
                    del self.slot_items[slot]
                    self.show_status_message(f"{item_name} unequipped")
                else:
                    displaced_item = self.slot_items.get(slot)
                    if current_slot is not None:
                        if displaced_item is None:
                            self.slot_items.pop(current_slot)
                        else:
                            self.slot_items[current_slot] = displaced_item
                    self.slot_items[slot] = item_name
                    self.show_status_message(
                        f"{item_name} equipped in slot {slot}"
                    )
                self.inventory_menu_item = None
                return

            clicked_item = self.ui.inventory_item_at(
                x,
                y,
                self.window.width,
                self.window.height,
                self.inventory,
            )
            self.inventory_menu_item = clicked_item
            return

        equipped_item = self.slot_items.get(self.ui.selected_slot)
        if equipped_item in ITEMS:
            self.use_inventory_item(equipped_item)
        else:
            self.attack(x, y)


def main():
    # Load dimensions before creating the window, then show the level-aware menu.
    level = load_level()
    window = arcade.Window(level.width, level.height, SCREEN_TITLE)
    window.show_view(MenuView(level))
    arcade.run()


if __name__ == "__main__":
    main()
