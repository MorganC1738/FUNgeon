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
Enemies use the abilities listed for their type in `ENEMY_TYPES`. Ranged shots
travel toward the player's position when fired; dashes burst toward the player
and can deal damage on contact. If health reaches zero, press Enter to restart
or Escape to return to the menu. Press Tab to open or close the inventory;
matching items stack, and the inventory displays up to four items per row.
Click any inventory item and choose slot 1 or 2 to equip it; choosing its
current slot unequips it. Select a slot with 1 or 2, then click anywhere in the
game to use its consumable. Weapons still attack toward the mouse.

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
block 12 5
block 12 6
block 12 7
```

`size <width> <height>` sets the room dimensions in pixels. Add exactly one
`player <x> <y>` spawn. Add any number of `chest <x> <y>` directives and
`enemy <type> <x> <y>` directives. Enemy types must match keys in
`ENEMY_TYPES` in `fungeon_enemies.py`. Positions are pixel coordinates from the
bottom-left corner and must be within the room. `block <column> <row>` places
a visible stone tile on a 40-pixel grid, with zero-based cell coordinates
starting at the room's bottom-left. Blocks stop player and enemy movement and
enemy projectiles; enemies route around them. Block cells must be in bounds and
cannot overlap a spawn, duplicate another block, or obstruct the room exit.
Levels 1 and 4 include sample obstacles.
To create another level, make a text file using this format and change
`DEFAULT_LEVEL_PATH` in `fungeon_level.py` to point to it.

Defeat every enemy in a room to reveal a thin exit at the top center, flush
against the back wall. Walk into it to load a randomly chosen different level.
Health, inventory, and equipped slots carry between rooms.

Available enemy types are `slime`, `skeleton`, `orc`, `bat`, `spider`, `golem`,
`wraith`, `boss`, `storm_tyrant`, and `frost_colossus`. Each type has its own
damage, health, size, speed, kill points, attack range, and attack cooldown in
`fungeon_enemies.py`. Levels 4-7 provide sample layouts with varied enemy
groups and difficulty; levels 8-10 are arenas for The Dreadlord, Storm Tyrant,
and Frost Colossus.

Enemy abilities are configured as a list on each entry in `ENEMY_TYPES`:

| Ability | Behavior |
| --- | --- |
| `melee` | Deals damage when the player is within the enemy's `attack_range`. |
| `ranged` | Fires a visible projectile that travels toward the player's position. Configure `ranged_range` and `projectile_speed`. |
| `dash` | Bursts toward the player and damages on contact. Configure `dash_trigger_range`, `dash_speed_multiplier`, `dash_duration`, and `dash_cooldown`. |
| `radial_burst` | Boss-only volley fired evenly in every direction. |
| `aimed_fan` | Boss-only spread of shots aimed at the player. |
| `cross_burst` | Boss-only rotating ring of shots; its starting angle shifts each volley. |

Current assignments: Slime and Golem use `melee`; Skeleton and Spider use
`melee` and `ranged`; Orc and Bat use `melee` and `dash`; Wraith uses all
three. The Dreadlord combines melee and dashing with a ten-shot radial burst;
the faster Storm Tyrant dashes frequently and fires a seven-shot aimed fan;
the slow, durable Frost Colossus launches rotating eight-shot cross volleys.
Bosses have a large health bar at the top of the screen. Add supported ability
names to an enemy's `abilities` list to enable them.

Chest drops are weapons listed in `WEAPONS` in `fungeon_loot.py`. Weapons have
four attack shapes: `slash` sweeps an aimed arc, `stab` thrusts in a narrow
line, `slam` hits a broad box in front of the player, and `spin` hits all
nearby enemies around the player. Every weapon defines its own rarity, range,
damage, cooldown, and attack size/arc, so weapons sharing a shape still feel
different. The inventory shows each weapon's attack style and stats.

Chest rarity is rolled when a chest spawns. Common, uncommon, rare, epic, and
legendary chests have increasingly favorable odds for higher-rarity weapons.
Common chests drop 1-4 items; uncommon drop 2-5, rare drop 3-5, and epic or
legendary drop 3-6 or 4-6. No chest can drop more than six items, and weapon
rarities become progressively less likely in lower-rarity chests. Every chest
contains at least one weapon; each remaining drop slot favors a consumable
nine-to-one over another weapon.

Consumables can be equipped to a slot and activated by clicking anywhere in the
game. Their effects are:

| Item | Effect |
| --- | --- |
| Health potion | Restores 35 health, up to the player's maximum. It is not consumed at full health. |
| Bomb | Drops at the player's position, shows its 115-pixel blast radius, then explodes after one second for 45 damage. |
| Smoke bomb | Stuns enemies within 190 pixels for 1.8 seconds. |
| Ward rune | Adds 60 shield points that absorb incoming damage before health. |
| Chain lightning | Deals 52 damage to up to the three nearest enemies within 280 pixels; bright lightning links show each strike. |
| Berserker draught | Increases weapon damage by 50% for 8 seconds. |
| Frost mine | Deals 32 damage and stuns enemies within 145 pixels for 2.4 seconds. |
| Phoenix feather | Restores up to 100 health and adds 25 shield points. |
| Time-stop crystal | Stuns all enemies in the room for 3 seconds. |
| Void bomb | Drops at the player's position, shows its 260-pixel blast radius, then explodes after one second for 105 damage. |

Active shield and berserker effects are displayed above the equipment slots at
the bottom right. Duplicate drops stack, each activation consumes one item,
and a depleted consumable is automatically unequipped.
