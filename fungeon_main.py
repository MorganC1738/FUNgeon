"""Arcade views and the main gameplay loop for FUNgeon."""

import math

import arcade

from fungeon_UI import FungeonUI
from fungeon_enemies import Enemy
from fungeon_loot import (
    CHEST_HEIGHT,
    LOOT_ITEM_RADIUS,
    Chest,
    WEAPONS,
    spawn_loot,
)
from fungeon_level import Level, load_level, next_level_path


# Default room dimensions are overridden by the selected text level.
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
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
SLASH_ARC_ANGLE = 72
DOOR_WIDTH = 110
DOOR_HEIGHT = 14
STATUS_FADE_START = 2.0
STATUS_FADE_END = 3.0
MAX_STATUS_MESSAGES = 5
STATUS_MESSAGE_LINE_HEIGHT = 24


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
            self.window.show_view(GameView(self.level))
        elif key == arcade.key.ESCAPE:
            self.window.show_view(MenuView(self.level))


class GameView(arcade.View):
    """Owns the current room state and connects input, game logic, and drawing."""

    def __init__(self, level: Level | None = None):
        super().__init__()
        self.level = level if level is not None else load_level()
        # Instantiate room entities from the parsed level spawn records.
        self.player_x, self.player_y = self.level.player_start
        self.held_keys = set()
        self.chests = [Chest(x, y) for x, y in self.level.chests]
        self.ground_items = []
        self.status_messages: list[tuple[str, float]] = []
        self.health = 100
        self.max_health = 100
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
            Enemy(enemy_type, x, y)
            for enemy_type, x, y in self.level.enemies
        ]
        self.slash_angle = 0
        self.slash_elapsed = SLASH_DURATION
        self.attack_cooldown_remaining = 0
        self.slash_range = WEAPONS["training sword"]["range"]

    def on_show_view(self):
        self.window.background_color = BACKGROUND

    def on_draw(self):
        # Draw the room and entities first, then HUD prompts and overlays.
        self.clear()
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
                    "Press E to open chest",
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
                self.window.height - 32 - index * STATUS_MESSAGE_LINE_HEIGHT,
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
        nearby_chests = [
            chest
            for chest in self.chests
            if (self.player_x - chest.center_x) ** 2
            + (self.player_y - chest.center_y) ** 2
            <= CHEST_INTERACTION_RANGE**2
        ]
        if not nearby_chests:
            return None
        return min(
            nearby_chests,
            key=lambda chest: (
                (self.player_x - chest.center_x) ** 2
                + (self.player_y - chest.center_y) ** 2
            ),
        )

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
        self.player_x, self.player_y = self.level.player_start
        self.chests = [Chest(x, y) for x, y in self.level.chests]
        self.enemies = [
            Enemy(enemy_type, x, y)
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
        if not self.ground_items:
            return None

        closest_item = min(
            self.ground_items,
            key=lambda item: (
                (self.player_x - item.center_x) ** 2
                + (self.player_y - item.center_y) ** 2
            ),
        )
        distance_squared = (
            (self.player_x - closest_item.center_x) ** 2
            + (self.player_y - closest_item.center_y) ** 2
        )
        if distance_squared <= LOOT_PICKUP_RANGE**2:
            return closest_item
        return None

    def damage_player(self, amount):
        self.health = max(0, self.health - max(0, amount))

    def heal_player(self, amount):
        self.health = min(self.max_health, self.health + max(0, amount))

    def draw_slash(self):
        if self.slash_elapsed >= SLASH_DURATION:
            return

        # Animate the slash arc around the cursor's direction from the player.
        progress = self.slash_elapsed / SLASH_DURATION
        sweep = math.radians(SLASH_ARC_ANGLE)
        arc_half_width = math.radians(21)
        arc_center = self.slash_angle - sweep / 2 + sweep * progress
        arcade.draw_arc_outline(
            self.player_x,
            self.player_y,
            self.slash_range * 2,
            self.slash_range * 2,
            (255, 240, 170, 230),
            math.degrees(arc_center - arc_half_width),
            math.degrees(arc_center + arc_half_width),
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
        self.slash_elapsed = 0
        self.attack_cooldown_remaining = weapon["cooldown"]

        for enemy in self.enemies:
            if not enemy.is_alive:
                continue

            # Hit enemies inside both the weapon's reach and its facing arc.
            health_before_attack = enemy.health
            offset_x = enemy.center_x - self.player_x
            offset_y = enemy.center_y - self.player_y
            distance = math.hypot(offset_x, offset_y)
            enemy_angle = math.atan2(offset_y, offset_x)
            angle_difference = math.atan2(
                math.sin(enemy_angle - self.slash_angle),
                math.cos(enemy_angle - self.slash_angle),
            )
            if (
                distance <= weapon["range"] + enemy.size
                and abs(angle_difference) <= math.radians(SLASH_ARC_ANGLE / 2)
            ):
                enemy.take_damage(weapon["damage"])
                if health_before_attack > 0 and not enemy.is_alive:
                    self.score += enemy.points

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

        if self.room_is_cleared and self.is_player_at_exit:
            self.advance_to_next_room()
            return

        self.slash_elapsed = min(
            SLASH_DURATION,
            self.slash_elapsed + delta_time,
        )
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

        length = (horizontal**2 + vertical**2) ** 0.5
        if length:
            # Normalize diagonal movement so it is not faster than straight movement.
            self.player_x += horizontal / length * PLAYER_SPEED * delta_time
            self.player_y += vertical / length * PLAYER_SPEED * delta_time

        # Keep the player within the room, clear of the HUD strip.
        self.player_x = max(22, min(self.window.width - 22, self.player_x))
        self.player_y = max(58, min(self.window.height - 22, self.player_y))

        for enemy in self.enemies:
            # Enemy.update returns damage only when an attack cooldown completes.
            incoming_damage = enemy.update(
                self.player_x,
                self.player_y,
                delta_time,
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
                        self.show_status_message("The chest spilled its loot!")
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

        self.attack(x, y)


def main():
    # Load dimensions before creating the window, then show the level-aware menu.
    level = load_level()
    window = arcade.Window(level.width, level.height, SCREEN_TITLE)
    window.show_view(MenuView(level))
    arcade.run()


if __name__ == "__main__":
    main()
