"""Parser and navigation helpers for the plain-text room files."""

from dataclasses import dataclass
from pathlib import Path
import random

from fungeon_enemies import ENEMY_TYPES


DEFAULT_LEVEL_PATH = Path(__file__).parent / "levels" / "level1.txt"


@dataclass(frozen=True)
class Level:
    """Parsed room data consumed by the game view."""

    width: int
    height: int
    player_start: tuple[float, float]
    chests: tuple[tuple[float, float], ...]
    enemies: tuple[tuple[str, float, float], ...]
    source_path: Path


def load_level(path=DEFAULT_LEVEL_PATH):
    """Read a directive-based level file and validate its entities and positions."""
    width = None
    height = None
    player_start = None
    chests = []
    enemies = []

    with Path(path).open(encoding="utf-8") as level_file:
        for line_number, raw_line in enumerate(level_file, start=1):
            # Ignore blank lines and inline comments so level files stay readable.
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue

            parts = line.split()
            directive = parts[0]
            try:
                # Parse each supported directive and reject malformed entries.
                if directive == "size" and len(parts) == 3:
                    if width is not None:
                        raise ValueError("level size can only be defined once")
                    width, height = int(parts[1]), int(parts[2])
                    if width <= 0 or height <= 0:
                        raise ValueError("level dimensions must be positive")
                elif directive == "player" and len(parts) == 3:
                    if player_start is not None:
                        raise ValueError("only one player spawn is allowed")
                    player_start = (float(parts[1]), float(parts[2]))
                elif directive == "chest" and len(parts) == 3:
                    chests.append((float(parts[1]), float(parts[2])))
                elif directive == "enemy" and len(parts) == 4:
                    enemy_type = parts[1].lower()
                    if enemy_type not in ENEMY_TYPES:
                        raise ValueError(f"unknown enemy type {enemy_type!r}")
                    enemies.append(
                        (enemy_type, float(parts[2]), float(parts[3]))
                    )
                else:
                    raise ValueError(f"invalid level directive: {line!r}")
            except ValueError as error:
                raise ValueError(
                    f"{path}:{line_number}: {error}"
                ) from error

    if width is None or height is None:
        raise ValueError(f"{path}: level must define size <width> <height>")
    if player_start is None:
        raise ValueError(f"{path}: level must define exactly one player spawn")

    positions = [player_start, *chests]
    positions.extend((x, y) for _, x, y in enemies)
    # Catch invalid spawns here rather than letting entities start off-room.
    for x, y in positions:
        if not (0 <= x <= width and 0 <= y <= height):
            raise ValueError(
                f"{path}: entity position ({x:g}, {y:g}) is outside "
                f"the level bounds ({width}, {height})"
            )

    return Level(
        width=width,
        height=height,
        player_start=player_start,
        chests=tuple(chests),
        enemies=tuple(enemies),
        source_path=Path(path).resolve(),
    )


def next_level_path(current_path=DEFAULT_LEVEL_PATH):
    """Choose a random level, preferring a different room when possible."""
    # Find all authored rooms; avoid immediately repeating the current one
    # unless it is the only available level.
    level_paths = sorted(
        DEFAULT_LEVEL_PATH.parent.glob("level*.txt")
    )
    if not level_paths:
        raise FileNotFoundError("No level files were found in the levels directory.")

    resolved_current = Path(current_path).resolve()
    other_levels = [
        path for path in level_paths if path.resolve() != resolved_current
    ]
    return random.choice(other_levels or level_paths)