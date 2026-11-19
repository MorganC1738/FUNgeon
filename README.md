# FUNgeon
Final Project/ Passion Project

## Run

Install Arcade 3.x and start the game:

```bash
python -m pip install "arcade>=3,<4"
python fungeon_main.py
```

Press Enter or click in the menu to start. Move with WASD or the arrow keys.
Approach a chest and press E to open it. Weapons spill onto the floor; move
near one and press E to pick it up. The player starts with a Training Sword
equipped in slot 1. Select a weapon slot with keys 1 or 2 and click in the
direction of the mouse to attack. Weapon range, damage, and cooldown depend on
the equipped weapon. Enemy kills award points shown in the top-left score.
Press F to spawn a chest at the player's current location.
Enemies chase the player and deal damage when they get close. If health reaches
zero, press Enter to restart or Escape to return to the menu. Press Tab to open
or close the inventory; matching weapons stack, and the inventory displays up
to four items per row. Click an inventory weapon and choose slot 1 or 2 to
equip it; equipping into an occupied slot swaps weapons, and choosing its
current slot unequips it.

## Level files

The game loads `levels/level1.txt` when it starts. It is a line-based text
format: blank lines and anything after `#` are ignored. Use one directive per
line:

```text
size 800 600
player 400 100
chest 400 300
enemy slime 250 450
enemy skeleton 400 500
enemy orc 550 450
```

`size <width> <height>` sets the room dimensions in pixels. Add exactly one
`player <x> <y>` spawn. Add any number of `chest <x> <y>` directives and
`enemy <type> <x> <y>` directives. Enemy types must match keys in
`ENEMY_TYPES` in `fungeon_enemies.py`. Positions are pixel coordinates from the
bottom-left corner and must be within the room.
To create another level, make a text file using this format and change
`DEFAULT_LEVEL_PATH` in `fungeon_level.py` to point to it.

Defeat every enemy in a room to reveal a thin exit at the top center, flush
against the back wall. Walk into it to load a randomly chosen different level.
Health, inventory, and equipped slots carry between rooms.

Available enemy types are `slime`, `skeleton`, `orc`, `bat`, `spider`, `golem`,
and `wraith`. Each type has its own damage, health, size, speed, kill points,
attack range, and attack cooldown in `fungeon_enemies.py`. Levels 4-7 provide
sample layouts with varied enemy groups and difficulty.

Chest drops are weapons listed in `WEAPONS` in `fungeon_loot.py`. Each weapon
defines a rarity, drop quantity, attack range, damage, and cooldown. Higher
rarities have greater range and damage and shorter cooldowns.
