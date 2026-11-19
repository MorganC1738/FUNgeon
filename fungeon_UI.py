"""Drawing and mouse hit-testing for the game HUD and inventory."""

import arcade

from fungeon_loot import LOOT_COLORS, WEAPONS


HEALTH_BACKGROUND = (75, 43, 52)
HEALTH_FILL = (220, 65, 78)
SLOT_BACKGROUND = (48, 56, 78)
SLOT_UNSELECTED = (105, 112, 128)
SLOT_SELECTED = (100, 220, 170)
TEXT_COLOR = (240, 244, 255)
RARITY_COLORS = {
    "common": (205, 210, 220),
    "uncommon": (100, 220, 140),
    "rare": (90, 160, 255),
    "epic": (190, 110, 255),
    "legendary": (255, 190, 70),
    "mythic": (255, 95, 160),
}


class FungeonUI:
    """Render the health bar, weapon slots, and inventory overlay."""

    def __init__(self):
        self.selected_slot = 1

    def select_slot(self, slot):
        if slot not in (1, 2):
            raise ValueError("Slot must be 1 or 2.")
        self.selected_slot = slot

    def draw(
        self,
        screen_width,
        screen_height,
        health,
        max_health,
        inventory,
        slot_items,
    ):
        self._draw_health_bar(health, max_health)
        self._draw_slots(screen_width, screen_height, inventory, slot_items)

    def draw_inventory(
        self,
        screen_width,
        screen_height,
        inventory,
        slot_items,
        selected_item,
    ):
        # Dim the game behind the inventory so the item grid is easy to read.
        arcade.draw_rect_filled(
            arcade.XYWH(
                screen_width / 2,
                screen_height / 2,
                screen_width,
                screen_height,
            ),
            (12, 15, 25, 220),
        )
        arcade.draw_text(
            "INVENTORY",
            screen_width / 2,
            screen_height - 70,
            TEXT_COLOR,
            font_size=32,
            bold=True,
            anchor_x="center",
        )
        arcade.draw_text(
            "Press TAB to close",
            screen_width / 2,
            screen_height - 102,
            TEXT_COLOR,
            font_size=14,
            anchor_x="center",
        )

        columns = 4
        box_width = 140
        box_height = 96
        gap = 14
        row_height = box_height + gap
        entries = list(inventory.items())
        grid_width = columns * box_width + (columns - 1) * gap
        grid_left = (screen_width - grid_width) / 2
        grid_top = screen_height - 145

        for index, (item_name, (amount, rarity)) in enumerate(entries):
            # Use a fixed four-column grid; extra inventory entries wrap below.
            x, y = self._inventory_item_center(
                index,
                grid_left,
                grid_top,
                box_width,
                box_height,
                gap,
                row_height,
            )
            rarity_color = RARITY_COLORS.get(rarity, SLOT_SELECTED)
            item_color = LOOT_COLORS.get(item_name, TEXT_COLOR)

            arcade.draw_rect_filled(
                arcade.XYWH(x, y, box_width, box_height),
                SLOT_BACKGROUND,
            )
            arcade.draw_rect_outline(
                arcade.XYWH(x, y, box_width, box_height),
                rarity_color,
                border_width=5 if item_name == selected_item else 3,
            )
            arcade.draw_circle_filled(x - 43, y + 9, 17, item_color)
            arcade.draw_circle_outline(
                x - 43,
                y + 9,
                17,
                rarity_color,
                border_width=2,
            )
            arcade.draw_text(
                item_name[:1].upper(),
                x - 43,
                y + 9,
                SLOT_BACKGROUND,
                font_size=16,
                bold=True,
                anchor_x="center",
                anchor_y="center",
            )
            arcade.draw_text(
                item_name,
                x + 5,
                y + 15,
                TEXT_COLOR,
                font_size=14,
                bold=True,
                anchor_x="center",
            )
            arcade.draw_text(
                rarity,
                x + 5,
                y - 5,
                rarity_color,
                font_size=12,
                anchor_x="center",
            )
            weapon = WEAPONS[item_name]
            arcade.draw_text(
                f"DMG {weapon['damage']}  RNG {weapon['range']:g}  "
                f"CD {weapon['cooldown']:g}s",
                x + 5,
                y - 23,
                TEXT_COLOR,
                font_size=9,
                anchor_x="center",
            )
            # Keep the stack count anchored at the lower-left of each item box.
            arcade.draw_text(
                f"{amount}x",
                x - box_width / 2 + 10,
                y - box_height / 2 + 8,
                TEXT_COLOR,
                font_size=14,
                bold=True,
            )
            equipped_slots = [
                str(slot)
                for slot, equipped_item in slot_items.items()
                if equipped_item == item_name
            ]
            if equipped_slots:
                arcade.draw_text(
                    "Slot " + ", ".join(equipped_slots),
                    x + box_width / 2 - 10,
                    y - box_height / 2 + 8,
                    TEXT_COLOR,
                    font_size=11,
                    anchor_x="right",
                )

        if selected_item in inventory:
            self._draw_inventory_dropdown(
                screen_width,
                screen_height,
                inventory,
                slot_items,
                selected_item,
            )

        if not entries:
            arcade.draw_text(
                "Your inventory is empty",
                screen_width / 2,
                screen_height / 2,
                TEXT_COLOR,
                font_size=18,
                anchor_x="center",
            )

    def inventory_item_at(self, x, y, screen_width, screen_height, inventory):
        """Return the inventory item under the cursor, if any."""
        box_width = 140
        box_height = 96
        gap = 14
        grid_left = (screen_width - (4 * box_width + 3 * gap)) / 2
        grid_top = screen_height - 145

        for index, item_name in enumerate(inventory):
            center_x, center_y = self._inventory_item_center(
                index,
                grid_left,
                grid_top,
                box_width,
                box_height,
                gap,
                box_height + gap,
            )
            if (
                center_x - box_width / 2 <= x <= center_x + box_width / 2
                and center_y - box_height / 2 <= y <= center_y + box_height / 2
            ):
                return item_name
        return None

    def inventory_menu_option_at(
        self,
        x,
        y,
        screen_width,
        screen_height,
        inventory,
        selected_item,
    ):
        """Map clicks in the selected item's dropdown rows to slot numbers."""
        if selected_item not in inventory:
            return None

        menu_x, menu_y = self._inventory_dropdown_center(
            screen_width,
            screen_height,
            inventory,
            selected_item,
        )
        menu_width = 150
        menu_height = 76
        if not (
            menu_x - menu_width / 2 <= x <= menu_x + menu_width / 2
            and menu_y - menu_height / 2 <= y <= menu_y + menu_height / 2
        ):
            return None

        # Each full menu row is clickable, not only the text glyphs.
        if menu_y + 4 <= y <= menu_y + 34:
            return 1
        if menu_y - 34 <= y <= menu_y - 4:
            return 2
        return None

    def _draw_inventory_dropdown(
        self,
        screen_width,
        screen_height,
        inventory,
        slot_items,
        selected_item,
    ):
        # An equipped item's current slot becomes an unequip action.
        equipped_slot = next(
            (
                slot
                for slot, item_name in slot_items.items()
                if item_name == selected_item
            ),
            None,
        )
        options = [f"Equip to slot {slot}" for slot in (1, 2)]
        if equipped_slot is not None:
            options[equipped_slot - 1] = f"Unequip from slot {equipped_slot}"

        x, y = self._inventory_dropdown_center(
            screen_width,
            screen_height,
            inventory,
            selected_item,
        )
        arcade.draw_rect_filled(
            arcade.XYWH(x, y, 150, 76),
            (30, 36, 52),
        )
        arcade.draw_rect_outline(
            arcade.XYWH(x, y, 150, 76),
            SLOT_SELECTED,
            border_width=2,
        )
        arcade.draw_rect_filled(
            arcade.XYWH(x, y + 19, 138, 30),
            (48, 56, 78),
        )
        arcade.draw_rect_filled(
            arcade.XYWH(x, y - 19, 138, 30),
            (48, 56, 78),
        )
        for index, option in enumerate(options):
            arcade.draw_text(
                option,
                x,
                y + 19 if index == 0 else y - 19,
                TEXT_COLOR,
                font_size=13,
                anchor_x="center",
                anchor_y="center",
            )

    def _inventory_dropdown_center(
        self,
        screen_width,
        screen_height,
        inventory,
        selected_item,
    ):
        # Keep the menu attached to its selected item while clamping it on-screen.
        box_width = 140
        box_height = 96
        gap = 14
        grid_left = (screen_width - (4 * box_width + 3 * gap)) / 2
        grid_top = screen_height - 145
        index = list(inventory).index(selected_item)
        item_x, item_y = self._inventory_item_center(
            index,
            grid_left,
            grid_top,
            box_width,
            box_height,
            gap,
            box_height + gap,
        )
        menu_x = min(
            max(item_x, 150 / 2 + 8),
            screen_width - 150 / 2 - 8,
        )
        menu_y = min(
            max(item_y - box_height / 2 - 76 / 2 - 4, 76 / 2 + 8),
            screen_height - 76 / 2 - 8,
        )
        return menu_x, menu_y

    @staticmethod
    def _inventory_item_center(
        index,
        grid_left,
        grid_top,
        box_width,
        box_height,
        gap,
        row_height,
    ):
        column = index % 4
        row = index // 4
        x = grid_left + column * (box_width + gap) + box_width / 2
        y = grid_top - row * row_height - box_height / 2
        return x, y

    def _draw_health_bar(self, health, max_health):
        # Clip the fill ratio so health changes always stay within the bar.
        left = 22
        bottom = 23
        width = 230
        height = 20
        health_ratio = max(0, min(1, health / max_health)) if max_health > 0 else 0

        arcade.draw_text(
            f"Health: {max(0, health):g} / {max_health:g}",
            left,
            bottom + height + 5,
            TEXT_COLOR,
            font_size=13,
        )
        arcade.draw_rect_filled(
            arcade.XYWH(left + width / 2, bottom + height / 2, width, height),
            HEALTH_BACKGROUND,
        )
        if health_ratio > 0:
            arcade.draw_rect_filled(
                arcade.XYWH(
                    left + width * health_ratio / 2,
                    bottom + height / 2,
                    width * health_ratio,
                    height - 4,
                ),
                HEALTH_FILL,
            )
        arcade.draw_rect_outline(
            arcade.XYWH(left + width / 2, bottom + height / 2, width, height),
            TEXT_COLOR,
            border_width=2,
        )

    def _draw_slots(self, screen_width, screen_height, inventory, slot_items):
        # Keep two fixed HUD positions; selection changes size and brightness.
        selected_size = 64
        unselected_size = 52
        gap = 12
        right_margin = 20
        bottom = 8
        group_width = selected_size * 2 + gap
        left = screen_width - right_margin - group_width

        for slot in (1, 2):
            selected = slot == self.selected_slot
            size = selected_size if selected else unselected_size
            cell_left = left + (slot - 1) * (selected_size + gap)
            x = cell_left + selected_size / 2
            y = bottom + size / 2
            item_name = slot_items.get(slot)
            item_data = inventory.get(item_name) if item_name else None
            if item_data:
                rarity_color = RARITY_COLORS.get(item_data[1], SLOT_SELECTED)
                color = rarity_color if selected else tuple(
                    int(channel * 0.55) for channel in rarity_color
                )
            else:
                color = SLOT_SELECTED if selected else SLOT_UNSELECTED

            arcade.draw_rect_filled(
                arcade.XYWH(x, y, size, size),
                SLOT_BACKGROUND if selected else (38, 43, 57),
            )
            arcade.draw_rect_outline(
                arcade.XYWH(x, y, size, size),
                color,
                border_width=3 if selected else 2,
            )
            if item_name and item_data:
                # Weapon initials stand in for art, with rarity coloring the border.
                icon_color = LOOT_COLORS.get(item_name, TEXT_COLOR)
                arcade.draw_circle_filled(x, y + 3, size * 0.25, icon_color)
                arcade.draw_circle_outline(
                    x,
                    y + 3,
                    size * 0.25,
                    color,
                    border_width=2,
                )
                arcade.draw_text(
                    item_name[:1].upper(),
                    x,
                    y + 3,
                    SLOT_BACKGROUND,
                    font_size=17 if selected else 14,
                    bold=True,
                    anchor_x="center",
                    anchor_y="center",
                )
                arcade.draw_text(
                    str(slot),
                    x,
                    bottom + 3,
                    color,
                    font_size=11,
                    bold=True,
                    anchor_x="center",
                )
            else:
                arcade.draw_text(
                    str(slot),
                    x,
                    y,
                    color,
                    font_size=22 if selected else 17,
                    bold=selected,
                    anchor_x="center",
                    anchor_y="center",
                )