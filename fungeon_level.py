"""Parser and navigation helpers for the plain-text room files."""

from dataclasses import dataclass
from pathlib import Path
import random

from fungeon_enemies import ENEMY_TYPES
from fungeon_obstacles import BlockGrid, GRID_SIZE


DEFAULT_LEVEL_PATH = Path(__file__).parent / "levels" / "level1.txt"


@dataclass(frozen=True)
class Level:
    """Parsed room data consumed by the game view."""

    width: int
    height: int
    player_start: tuple[float, float]
    chests: tuple[tuple[float, float], ...]
    enemies: tuple[tuple[str, float, float], ...]
    blocks: tuple[tuple[int, int], ...]
    source_path: Path


def load_level(path=DEFAULT_LEVEL_PATH):
    """Read a directive-based level file and validate its entities and positions."""
    width = None
    height = None
    player_start = None
    chests = []
    enemies = []
    blocks = []

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
                elif directive == "block" and len(parts) == 3:
                    blocks.append((int(parts[1]), int(parts[2])))
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

    columns = (width + GRID_SIZE - 1) // GRID_SIZE
    rows = (height + GRID_SIZE - 1) // GRID_SIZE
    block_grid = BlockGrid(width, height, blocks)
    for cell in blocks:
        column, row = cell
        if not (0 <= column < columns and 0 <= row < rows):
            raise ValueError(
                f"{path}: block cell ({column}, {row}) is outside the "
                f"{columns}x{rows} grid"
            )
        left, bottom, right, top = block_grid.cell_bounds(cell)
        exit_left = width / 2 - 77
        exit_right = width / 2 + 77
        if (
            right > exit_left
            and left < exit_right
            and top > height - 36
        ):
            raise ValueError(f"{path}: block cell {cell} overlaps the room exit")
    if len(set(blocks)) != len(blocks):
        raise ValueError(f"{path}: block cells cannot be duplicated")

    entity_positions = [(player_start[0], player_start[1], 22)]
    entity_positions.extend((x, y, 30) for x, y in chests)
    entity_positions.extend(
        (x, y, ENEMY_TYPES[enemy_type]["size"])
        for enemy_type, x, y in enemies
    )
    for x, y, _ in entity_positions:
        if not (0 <= x <= width and 0 <= y <= height):
            raise ValueError(
                f"{path}: entity position ({x:g}, {y:g}) is outside "
                f"the level bounds ({width}, {height})"
            )

    for x, y, radius in entity_positions:
        if block_grid.collides_circle(x, y, radius):
            raise ValueError(
                f"{path}: entity position ({x:g}, {y:g}) overlaps a block"
            )

    return Level(
        width=width,
        height=height,
        player_start=player_start,
        chests=tuple(chests),
        enemies=tuple(enemies),
        blocks=tuple(blocks),
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