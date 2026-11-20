"""Chest contents, dropped weapon visuals, and chest behavior."""

import math
import random
from typing import Literal, TypedDict

import arcade


# Restrict rarity values to the tiers used by the loot and UI systems.
Rarity = Literal["common", "uncommon", "rare", "epic", "legendary", "mythic"]
AttackType = Literal["slash", "stab", "slam", "spin"]
ChestRarity = Literal["common", "uncommon", "rare", "epic", "legendary"]


class LootDefinition(TypedDict):
    rarity: Rarity
    quantity: tuple[int, int]
    range: float
    damage: int
    cooldown: float
    attack_type: AttackType
    width: float
    arc_angle: float


class ItemDefinition(TypedDict):
    rarity: Rarity
    description: str
    effect: str
    value: int
    radius: int
    duration: float


class LootDrop(TypedDict):
    rarity: Rarity
    quantity: int


class ChestDefinition(TypedDict):
    color: tuple[int, int, int]
    item_count: tuple[int, int]
    rarity_weights: dict[Rarity, int]


CHEST_DARK = (82, 49, 32)
CHEST_TRIM = (240, 190, 75)
CHEST_WIDTH = 56
CHEST_HEIGHT = 42
LOOT_DROP_RADIUS = 105
LOOT_ITEM_RADIUS = 12
LOOT_ITEM_SPACING = LOOT_ITEM_RADIUS * 2 + 8

# Weapons use distinct attack shapes and trade reach, area, damage, and speed.
WEAPONS: dict[str, LootDefinition] = {
    "training sword": {
        "rarity": "common",
        "quantity": (1, 1),
        "range": 92,
        "damage": 10,
        "cooldown": 1.0,
        "attack_type": "slash",
        "width": 0,
        "arc_angle": 76,
    },
    "rusty dagger": {
        "rarity": "common",
        "quantity": (1, 2),
        "range": 82,
        "damage": 13,
        "cooldown": 0.48,
        "attack_type": "stab",
        "width": 22,
        "arc_angle": 0,
    },
    "woodcutter axe": {
        "rarity": "common",
        "quantity": (1, 1),
        "range": 78,
        "damage": 20,
        "cooldown": 1.3,
        "attack_type": "slam",
        "width": 90,
        "arc_angle": 0,
    },
    "iron sword": {
        "rarity": "uncommon",
        "quantity": (1, 1),
        "range": 112,
        "damage": 22,
        "cooldown": 0.82,
        "attack_type": "slash",
        "width": 0,
        "arc_angle": 92,
    },
    "duelist's rapier": {
        "rarity": "uncommon",
        "quantity": (1, 1),
        "range": 132,
        "damage": 24,
        "cooldown": 0.72,
        "attack_type": "stab",
        "width": 28,
        "arc_angle": 0,
    },
    "stone maul": {
        "rarity": "uncommon",
        "quantity": (1, 1),
        "range": 82,
        "damage": 31,
        "cooldown": 1.45,
        "attack_type": "slam",
        "width": 118,
        "arc_angle": 0,
    },
    "hunters spear": {
        "rarity": "rare",
        "quantity": (1, 1),
        "range": 158,
        "damage": 32,
        "cooldown": 0.9,
        "attack_type": "stab",
        "width": 34,
        "arc_angle": 0,
    },
    "moonfang sabre": {
        "rarity": "rare",
        "quantity": (1, 1),
        "range": 118,
        "damage": 29,
        "cooldown": 0.66,
        "attack_type": "slash",
        "width": 0,
        "arc_angle": 118,
    },
    "ironquake hammer": {
        "rarity": "rare",
        "quantity": (1, 1),
        "range": 92,
        "damage": 43,
        "cooldown": 1.55,
        "attack_type": "slam",
        "width": 142,
        "arc_angle": 0,
    },
    "flame greatsword": {
        "rarity": "epic",
        "quantity": (1, 1),
        "range": 136,
        "damage": 48,
        "cooldown": 0.95,
        "attack_type": "slash",
        "width": 0,
        "arc_angle": 106,
    },
    "needle of embers": {
        "rarity": "epic",
        "quantity": (1, 1),
        "range": 176,
        "damage": 42,
        "cooldown": 0.72,
        "attack_type": "stab",
        "width": 38,
        "arc_angle": 0,
    },
    "volcanic crusher": {
        "rarity": "epic",
        "quantity": (1, 1),
        "range": 105,
        "damage": 62,
        "cooldown": 1.65,
        "attack_type": "slam",
        "width": 166,
        "arc_angle": 0,
    },
    "cyclone chakram": {
        "rarity": "epic",
        "quantity": (1, 1),
        "range": 100,
        "damage": 27,
        "cooldown": 0.58,
        "attack_type": "spin",
        "width": 0,
        "arc_angle": 0,
    },
    "stormblade": {
        "rarity": "legendary",
        "quantity": (1, 1),
        "range": 155,
        "damage": 66,
        "cooldown": 0.76,
        "attack_type": "slash",
        "width": 0,
        "arc_angle": 132,
    },
    "sky-piercer": {
        "rarity": "legendary",
        "quantity": (1, 1),
        "range": 205,
        "damage": 58,
        "cooldown": 0.82,
        "attack_type": "stab",
        "width": 44,
        "arc_angle": 0,
    },
    "thunderhead maul": {
        "rarity": "legendary",
        "quantity": (1, 1),
        "range": 116,
        "damage": 86,
        "cooldown": 1.5,
        "attack_type": "slam",
        "width": 190,
        "arc_angle": 0,
    },
    "tempest orbit": {
        "rarity": "legendary",
        "quantity": (1, 1),
        "range": 132,
        "damage": 43,
        "cooldown": 0.52,
        "attack_type": "spin",
        "width": 0,
        "arc_angle": 0,
    },
    "void reaver": {
        "rarity": "mythic",
        "quantity": (1, 1),
        "range": 176,
        "damage": 88,
        "cooldown": 0.86,
        "attack_type": "slash",
        "width": 0,
        "arc_angle": 148,
    },
    "singularity lance": {
        "rarity": "mythic",
        "quantity": (1, 1),
        "range": 232,
        "damage": 82,
        "cooldown": 0.78,
        "attack_type": "stab",
        "width": 52,
        "arc_angle": 0,
    },
    "worldbreaker": {
        "rarity": "mythic",
        "quantity": (1, 1),
        "range": 126,
        "damage": 115,
        "cooldown": 1.55,
        "attack_type": "slam",
        "width": 220,
        "arc_angle": 0,
    },
    "event horizon": {
        "rarity": "mythic",
        "quantity": (1, 1),
        "range": 155,
        "damage": 58,
        "cooldown": 0.48,
        "attack_type": "spin",
        "width": 0,
        "arc_angle": 0,
    },
}

# Consumables have distinct effects and are grouped with weapon rarities.
ITEMS: dict[str, ItemDefinition] = {
    "health potion": {
        "rarity": "common",
        "description": "Restore 35 health",
        "effect": "heal",
        "value": 35,
        "radius": 0,
        "duration": 0,
    },
    "bomb": {
        "rarity": "common",
        "description": "Blast nearby enemies",
        "effect": "blast",
        "value": 45,
        "radius": 115,
        "duration": 0,
    },
    "smoke bomb": {
        "rarity": "uncommon",
        "description": "Stun enemies in a wide area",
        "effect": "stun",
        "value": 0,
        "radius": 190,
        "duration": 1.8,
    },
    "ward rune": {
        "rarity": "uncommon",
        "description": "Absorb the next 60 damage",
        "effect": "shield",
        "value": 60,
        "radius": 0,
        "duration": 0,
    },
    "chain lightning": {
        "rarity": "rare",
        "description": "Strike up to 3 distant enemies",
        "effect": "chain",
        "value": 52,
        "radius": 280,
        "duration": 0,
    },
    "berserker draught": {
        "rarity": "rare",
        "description": "Deal 50% more damage briefly",
        "effect": "damage_boost",
        "value": 50,
        "radius": 0,
        "duration": 8,
    },
    "frost mine": {
        "rarity": "epic",
        "description": "Freeze and wound nearby enemies",
        "effect": "frost",
        "value": 32,
        "radius": 145,
        "duration": 2.4,
    },
    "phoenix feather": {
        "rarity": "legendary",
        "description": "Restore 100 health and 25 shield",
        "effect": "phoenix",
        "value": 100,
        "radius": 0,
        "duration": 0,
    },
    "time-stop crystal": {
        "rarity": "mythic",
        "description": "Freeze every enemy for 3 seconds",
        "effect": "time_stop",
        "value": 0,
        "radius": 10000,
        "duration": 3,
    },
    "void bomb": {
        "rarity": "mythic",
        "description": "Devastate a large area",
        "effect": "void_blast",
        "value": 105,
        "radius": 260,
        "duration": 0,
    },
}

# Chest rarity controls its appearance, number of drops, and rarity odds.
CHEST_RARITIES: dict[ChestRarity, ChestDefinition] = {
    "common": {
        "color": (170, 125, 75),
        "item_count": (1, 4),
        "rarity_weights": {
            "common": 720,
            "uncommon": 210,
            "rare": 60,
            "epic": 9,
            "legendary": 1,
            "mythic": 0,
        },
    },
    "uncommon": {
        "color": (90, 190, 125),
        "item_count": (2, 5),
        "rarity_weights": {
            "common": 400,
            "uncommon": 350,
            "rare": 180,
            "epic": 55,
            "legendary": 14,
            "mythic": 1,
        },
    },
    "rare": {
        "color": (85, 145, 235),
        "item_count": (3, 5),
        "rarity_weights": {
            "common": 150,
            "uncommon": 300,
            "rare": 300,
            "epic": 160,
            "legendary": 70,
            "mythic": 20,
        },
    },
    "epic": {
        "color": (185, 105, 235),
        "item_count": (3, 6),
        "rarity_weights": {
            "common": 50,
            "uncommon": 150,
            "rare": 280,
            "epic": 270,
            "legendary": 180,
            "mythic": 70,
        },
    },
    "legendary": {
        "color": (245, 180, 65),
        "item_count": (4, 6),
        "rarity_weights": {
            "common": 10,
            "uncommon": 50,
            "rare": 160,
            "epic": 280,
            "legendary": 300,
            "mythic": 200,
        },
    },
}
CHEST_SPAWN_WEIGHTS: dict[ChestRarity, int] = {
    "common": 700,
    "uncommon": 200,
    "rare": 75,
    "epic": 22,
    "legendary": 3,
}
RARITY_ORDER: tuple[Rarity, ...] = (
    "common",
    "uncommon",
    "rare",
    "epic",
    "legendary",
    "mythic",
)

# Cache weapon and item pools; these catalogs are static during gameplay.
WEAPONS_BY_RARITY: dict[Rarity, tuple[str, ...]] = {
    rarity: tuple(
        name for name, weapon in WEAPONS.items()
        if weapon["rarity"] == rarity
    )
    for rarity in RARITY_ORDER
}
ITEMS_BY_RARITY: dict[Rarity, tuple[str, ...]] = {
    rarity: tuple(
        name for name, item in ITEMS.items()
        if item["rarity"] == rarity
    )
    for rarity in RARITY_ORDER
}
CHEST_DROP_OPTIONS = {
    chest_rarity: (
        tuple(
            rarity
            for rarity in RARITY_ORDER
            if definition["rarity_weights"][rarity] > 0
        ),
        tuple(
            definition["rarity_weights"][rarity]
            for rarity in RARITY_ORDER
            if definition["rarity_weights"][rarity] > 0
        ),
    )
    for chest_rarity, definition in CHEST_RARITIES.items()
}

# These colors distinguish item icons and rarity labels in the game and UI.
LOOT_COLORS = {
    "training sword": (185, 190, 200),
    "rusty dagger": (160, 125, 90),
    "woodcutter axe": (145, 105, 65),
    "iron sword": (155, 175, 195),
    "duelist's rapier": (190, 210, 220),
    "stone maul": (135, 125, 110),
    "hunters spear": (100, 190, 150),
    "moonfang sabre": (120, 185, 230),
    "ironquake hammer": (170, 125, 95),
    "flame greatsword": (240, 100, 60),
    "needle of embers": (255, 135, 80),
    "volcanic crusher": (215, 75, 45),
    "cyclone chakram": (225, 175, 255),
    "stormblade": (100, 180, 255),
    "sky-piercer": (150, 210, 255),
    "thunderhead maul": (255, 215, 95),
    "tempest orbit": (125, 235, 230),
    "void reaver": (190, 100, 255),
    "singularity lance": (205, 155, 255),
    "worldbreaker": (245, 90, 150),
    "event horizon": (145, 95, 235),
    "health potion": (225, 75, 95),
    "bomb": (245, 125, 55),
    "smoke bomb": (145, 155, 175),
    "ward rune": (105, 205, 225),
    "chain lightning": (255, 230, 85),
    "berserker draught": (225, 80, 65),
    "frost mine": (115, 205, 245),
    "phoenix feather": (255, 155, 65),
    "time-stop crystal": (110, 225, 220),
    "void bomb": (165, 80, 230),
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
    """One weapon or consumable dropped onto the floor for pickup."""

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

    def __init__(self, x, y, rarity: ChestRarity | None = None):
        if rarity is None:
            rarity = random.choices(
                tuple(CHEST_SPAWN_WEIGHTS),
                weights=tuple(CHEST_SPAWN_WEIGHTS.values()),
                k=1,
            )[0]
        if rarity not in CHEST_RARITIES:
            raise ValueError(f"Unknown chest rarity: {rarity}")
        self.center_x = x
        self.center_y = y
        self.rarity = rarity
        self.is_open = False

    def draw(self):
        # Change the lid appearance after the chest has been opened.
        chest_color = CHEST_RARITIES[self.rarity]["color"]
        arcade.draw_rect_filled(
            arcade.XYWH(self.center_x, self.center_y - 5, CHEST_WIDTH, 30),
            chest_color,
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
                chest_color,
            )
            arcade.draw_rect_filled(
                arcade.XYWH(self.center_x, self.center_y + 7, CHEST_WIDTH + 4, 5),
                CHEST_DARK,
            )
        arcade.draw_rect_filled(
            arcade.XYWH(self.center_x, self.center_y - 5, 8, 30),
            CHEST_TRIM if self.rarity == "common" else (255, 255, 235),
        )

    def open(self):
        """Mark the chest open and return its randomized loot."""
        if self.is_open:
            return {}

        self.is_open = True
        definition = CHEST_RARITIES[self.rarity]
        item_count = random.randint(*definition["item_count"])
        available_rarities, rarity_weights = CHEST_DROP_OPTIONS[self.rarity]

        loot: dict[str, LootDrop] = {}
        for drop_index in range(item_count):
            rarity = random.choices(
                available_rarities,
                weights=rarity_weights,
                k=1,
            )[0]
            # The first slot guarantees a weapon; later slots favor utility items.
            item_pool = (
                ITEMS_BY_RARITY[rarity]
                if drop_index and random.random() < 0.9
                else WEAPONS_BY_RARITY[rarity]
            )
            item = random.choice(item_pool)
            if item not in loot:
                loot[item] = {"rarity": rarity, "quantity": 0}
            loot[item]["quantity"] += 1
        return loot
