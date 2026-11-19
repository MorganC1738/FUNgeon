"""Chest contents, dropped weapon visuals, and chest behavior."""

import math
import random
from typing import Literal, TypedDict

import arcade


# Restrict rarity values to the tiers used by the loot and UI systems.
Rarity = Literal["common", "uncommon", "rare", "epic", "legendary", "mythic"]


class LootDefinition(TypedDict):
    rarity: Rarity
    quantity: tuple[int, int]
    range: float
    damage: int
    cooldown: float


class LootDrop(TypedDict):
    rarity: Rarity
    quantity: int


CHEST_COLOR = (135, 83, 45)
CHEST_DARK = (82, 49, 32)
CHEST_TRIM = (240, 190, 75)
CHEST_WIDTH = 56
CHEST_HEIGHT = 42
LOOT_DROP_RADIUS = 105
LOOT_ITEM_RADIUS = 12
LOOT_ITEM_SPACING = LOOT_ITEM_RADIUS * 2 + 8

# Weapon records provide their drop rarity, possible stack size, and combat stats.
WEAPONS: dict[str, LootDefinition] = {
    "training sword": {
        "rarity": "common",
        "quantity": (1, 1),
        "range": 92,
        "damage": 10,
        "cooldown": 1.0,
    },
    "rusty dagger": {
        "rarity": "common",
        "quantity": (1, 2),
        "range": 100,
        "damage": 14,
        "cooldown": 0.9,
    },
    "iron sword": {
        "rarity": "uncommon",
        "quantity": (1, 1),
        "range": 112,
        "damage": 22,
        "cooldown": 0.82,
    },
    "hunters spear": {
        "rarity": "rare",
        "quantity": (1, 1),
        "range": 124,
        "damage": 32,
        "cooldown": 0.76,
    },
    "flame greatsword": {
        "rarity": "epic",
        "quantity": (1, 1),
        "range": 136,
        "damage": 48,
        "cooldown": 0.70,
    },
    "stormblade": {
        "rarity": "legendary",
        "quantity": (1, 1),
        "range": 155,
        "damage": 66,
        "cooldown": 0.64,
    },
    "void reaver": {
        "rarity": "mythic",
        "quantity": (1, 1),
        "range": 176,
        "damage": 88,
        "cooldown": 0.58,
    },
}

# Keep the familiar chest_loot name as the table used when a chest is opened.
chest_loot = WEAPONS

# Each weapon gets an independent appearance roll based on its rarity.
RARITY_DROP_CHANCE: dict[Rarity, float] = {
    "common": 0.80,
    "uncommon": 0.55,
    "rare": 0.30,
    "epic": 0.15,
    "legendary": 0.07,
    "mythic": 0.02,
}

# These colors distinguish item icons and rarity labels in the game and UI.
LOOT_COLORS = {
    "training sword": (185, 190, 200),
    "rusty dagger": (160, 125, 90),
    "iron sword": (155, 175, 195),
    "hunters spear": (100, 190, 150),
    "flame greatsword": (240, 100, 60),
    "stormblade": (100, 180, 255),
    "void reaver": (190, 100, 255),
}
RARITY_COLORS = {
    "common": (205, 210, 220),
    "uncommon": (100, 220, 140),
    "rare": (90, 160, 255),
    "epic": (190, 110, 255),
    "legendary": (255, 190, 70),
    "mythic": (255, 95, 160),
}


class GroundItem:
    """One weapon stack dropped onto the floor and available for pickup."""

    def __init__(self, item: str, amount: int, rarity: Rarity, x: float, y: float):
        self.item = item
        self.amount = amount
        self.rarity = rarity
        self.center_x = x
        self.center_y = y

    def draw(self):
        # The colored token and labels show what dropped and how rare it is.
        color = LOOT_COLORS.get(self.item, (160, 210, 170))
        arcade.draw_circle_filled(
            self.center_x,
            self.center_y,
            LOOT_ITEM_RADIUS,
            color,
        )
        arcade.draw_circle_outline(
            self.center_x,
            self.center_y,
            LOOT_ITEM_RADIUS,
            CHEST_DARK,
            border_width=2,
        )
        arcade.draw_text(
            self.item,
            self.center_x,
            self.center_y - LOOT_ITEM_RADIUS - 16,
            color,
            font_size=11,
            anchor_x="center",
        )
        arcade.draw_text(
            self.rarity,
            self.center_x,
            self.center_y - LOOT_ITEM_RADIUS - 28,
            RARITY_COLORS[self.rarity],
            font_size=9,
            anchor_x="center",
        )


def spawn_loot(chest_x: float, chest_y: float, loot: dict[str, LootDrop]):
    """Create individual floor items scattered around a chest without overlap."""
    # Split each weapon quantity into separate pickups, then place each in a
    # random point within the chest's drop radius.
    items = [
        GroundItem(item, 1, drop["rarity"], chest_x, chest_y)
        for item, drop in loot.items()
        for _ in range(drop["quantity"])
    ]
    placed_positions = []

    for item in items:
        for _ in range(100):
            angle = random.uniform(0, 2 * math.pi)
            distance = LOOT_DROP_RADIUS * random.random() ** 0.5
            x = chest_x + distance * math.cos(angle)
            y = chest_y + distance * math.sin(angle)
            # Reject candidates too close to an already placed item.
            if all(
                (x - other_x) ** 2 + (y - other_y) ** 2
                >= LOOT_ITEM_SPACING**2
                for other_x, other_y in placed_positions
            ):
                item.center_x = x
                item.center_y = y
                placed_positions.append((x, y))
                break
        else:
            # Search spaced grid points if random attempts could not fit an item.
            fallback_positions = [
                (x, y)
                for x in range(
                    int(chest_x - LOOT_DROP_RADIUS),
                    int(chest_x + LOOT_DROP_RADIUS) + 1,
                    LOOT_ITEM_SPACING,
                )
                for y in range(
                    int(chest_y - LOOT_DROP_RADIUS),
                    int(chest_y + LOOT_DROP_RADIUS) + 1,
                    LOOT_ITEM_SPACING,
                )
                if (x - chest_x) ** 2 + (y - chest_y) ** 2
                <= LOOT_DROP_RADIUS**2
                and all(
                    (x - other_x) ** 2 + (y - other_y) ** 2
                    >= LOOT_ITEM_SPACING**2
                    for other_x, other_y in placed_positions
                )
            ]
            if not fallback_positions:
                raise ValueError("Too many loot items to place around the chest.")
            item.center_x, item.center_y = random.choice(fallback_positions)
            placed_positions.append((item.center_x, item.center_y))

    return items


class Chest:
    """A drawable, one-use chest that rolls weapon drops when opened."""

    def __init__(self, x, y):
        self.center_x = x
        self.center_y = y
        self.is_open = False

    def draw(self):
        # Change the lid appearance after the chest has been opened.
        arcade.draw_rect_filled(
            arcade.XYWH(self.center_x, self.center_y - 5, CHEST_WIDTH, 30),
            CHEST_COLOR,
        )
        arcade.draw_rect_filled(
            arcade.XYWH(self.center_x, self.center_y - 22, CHEST_WIDTH + 4, 5),
            CHEST_DARK,
        )
        if self.is_open:
            arcade.draw_rect_filled(
                arcade.XYWH(self.center_x, self.center_y + 20, CHEST_WIDTH, 10),
                CHEST_DARK,
            )
        else:
            arcade.draw_rect_filled(
                arcade.XYWH(self.center_x, self.center_y + 14, CHEST_WIDTH, 14),
                CHEST_COLOR,
            )
            arcade.draw_rect_filled(
                arcade.XYWH(self.center_x, self.center_y + 7, CHEST_WIDTH + 4, 5),
                CHEST_DARK,
            )
        arcade.draw_rect_filled(
            arcade.XYWH(self.center_x, self.center_y - 5, 8, 30),
            CHEST_TRIM,
        )

    def open(self):
        """Mark the chest open and return its randomized loot."""
        if self.is_open:
            return {}

        self.is_open = True
        loot: dict[str, LootDrop] = {}
        for item, definition in chest_loot.items():
            # Only successful rarity rolls drop; quantity bounds are inclusive.
            if random.random() < RARITY_DROP_CHANCE[definition["rarity"]]:
                loot[item] = {
                    "rarity": definition["rarity"],
                    "quantity": random.randint(*definition["quantity"]),
                }
        return loot
