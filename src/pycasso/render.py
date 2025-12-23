import hashlib
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from pycasso.config import Config
from pycasso.parse import Entity, EntityType


def _stable_hash(value: str) -> int:
    return int(hashlib.sha256(value.encode()).hexdigest()[:8], 16)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _saturate(color: tuple[int, int, int], factor: float = 1.2) -> tuple[int, int, int]:
    avg = sum(color) / 3
    return tuple(int(min(255, avg + (c - avg) * factor)) for c in color)  # type: ignore[return-value]


def _brighten(color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return tuple(int(min(255, c * factor)) for c in color)  # type: ignore[return-value]


def _get_color_for_entity(entity: Entity, config: Config) -> tuple[int, int, int]:
    color_map = {
        EntityType.CLASS: config.colors.class_color,
        EntityType.FUNCTION: config.colors.function,
        EntityType.LOOP: config.colors.loop,
        EntityType.CONDITIONAL: config.colors.conditional,
    }
    base = _hex_to_rgb(color_map[entity.entity_type])
    brightness = 1.0 + (entity.complexity / 20)
    return _brighten(_saturate(base, 1.3), brightness)


def _spiral_layout(index: int, total: int, center_x: int, center_y: int, max_radius: int) -> tuple[int, int]:
    if total == 1:
        return center_x, center_y
    angle = index * 2.4
    radius = max_radius * math.sqrt(index / total) * 0.85
    x = int(center_x + radius * math.cos(angle))
    y = int(center_y + radius * math.sin(angle))
    return x, y


def _draw_radial_gradient(draw: ImageDraw.ImageDraw, width: int, height: int, 
                          center_color: tuple[int, int, int], edge_color: tuple[int, int, int]) -> None:
    cx, cy = width // 2, height // 2
    max_dist = math.sqrt(cx**2 + cy**2)
    for ring in range(0, int(max_dist), 40):
        t = ring / max_dist
        r = int(center_color[0] + (edge_color[0] - center_color[0]) * t)
        g = int(center_color[1] + (edge_color[1] - center_color[1]) * t)
        b = int(center_color[2] + (edge_color[2] - center_color[2]) * t)
        draw.ellipse([cx - ring, cy - ring, cx + ring, cy + ring], outline=(r, g, b, 255), width=42)


def render(entities: list[Entity], config: Config, seed: int, output_path: Path) -> None:
    width = config.canvas.width
    height = config.canvas.height
    background = _hex_to_rgb(config.colors.background)
    
    bg_center = _brighten(background, 1.4)
    bg_edge = background

    image = Image.new("RGBA", (width, height), (*background, 255))
    draw = ImageDraw.Draw(image)
    
    _draw_radial_gradient(draw, width, height, bg_center, bg_edge)
    
    glow_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    
    connection_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    conn_draw = ImageDraw.Draw(connection_layer)

    if not entities:
        image.save(output_path, "PNG")
        return

    unique_files = sorted({e.file_path for e in entities}, key=lambda p: str(p))
    num_files = len(unique_files)
    
    margin = min(width, height) // 12
    usable_width = width - 2 * margin
    usable_height = height - 2 * margin
    center_x = width // 2
    center_y = height // 2
    
    file_centers: dict[Path, tuple[int, int]] = {}
    for i, file_path in enumerate(unique_files):
        fx, fy = _spiral_layout(i, num_files, center_x, center_y, min(usable_width, usable_height) // 2)
        file_centers[file_path] = (fx, fy)

    entities_by_file: dict[Path, list[Entity]] = {}
    for entity in entities:
        entities_by_file.setdefault(entity.file_path, []).append(entity)

    all_positions: list[tuple[int, int, Entity]] = []
    entity_positions: dict[tuple[Path, str], tuple[int, int]] = {}
    
    for file_path, file_entities in entities_by_file.items():
        fx, fy = file_centers[file_path]
        file_radius = 60 + len(file_entities) * 10
        
        glow_draw.ellipse(
            [fx - file_radius - 30, fy - file_radius - 30,
             fx + file_radius + 30, fy + file_radius + 30],
            fill=(255, 255, 255, 8)
        )
        
        for i, entity in enumerate(file_entities):
            rng = random.Random(seed + entity.fingerprint)
            
            angle = rng.uniform(0, 2 * math.pi)
            r = rng.uniform(0, file_radius)
            x = int(fx + r * math.cos(angle))
            y = int(fy + r * math.sin(angle))
            
            x = max(margin, min(width - margin, x))
            y = max(margin, min(height - margin, y))
            
            all_positions.append((x, y, entity))
            entity_positions[(file_path, entity.name)] = (x, y)

    all_positions.sort(key=lambda p: p[2].complexity)

    for file_path, file_entities in entities_by_file.items():
        classes = [e for e in file_entities if e.entity_type == EntityType.CLASS]
        functions = [e for e in file_entities if e.entity_type == EntityType.FUNCTION]
        
        for cls in classes:
            cls_pos = entity_positions.get((file_path, cls.name))
            if not cls_pos:
                continue
            for func in functions:
                func_pos = entity_positions.get((file_path, func.name))
                if not func_pos:
                    continue
                rng = random.Random(seed + cls.fingerprint + func.fingerprint)
                if rng.random() < 0.4:
                    conn_draw.line([cls_pos, func_pos], fill=(150, 80, 200, 40), width=1)

    for x, y, entity in all_positions:
        base_size = 20 + (entity.mass // 4)
        size = min(base_size + entity.complexity * 6, 100)
        
        color = _get_color_for_entity(entity, config)

        if entity.entity_type == EntityType.CLASS:
            half = size // 2
            for glow_offset in [12, 6, 3]:
                glow_draw.rectangle(
                    [x - half - glow_offset, y - half - glow_offset, 
                     x + half + glow_offset, y + half + glow_offset],
                    fill=(*color, 15)
                )
            draw.rectangle([x - half, y - half, x + half, y + half], fill=(*color, 180))
            draw.rectangle([x - half, y - half, x + half, y + half], outline=(255, 255, 255, 100), width=2)

        elif entity.entity_type == EntityType.FUNCTION:
            for glow_offset in [16, 10, 5]:
                alpha = 25 if entity.complexity > 5 else 15
                glow_draw.ellipse(
                    [x - size - glow_offset, y - size - glow_offset, 
                     x + size + glow_offset, y + size + glow_offset],
                    fill=(*color, alpha)
                )
            draw.ellipse([x - size, y - size, x + size, y + size], fill=(*color, 230))
            if entity.complexity > 5:
                inner = size // 3
                draw.ellipse([x - inner, y - inner, x + inner, y + inner], fill=(255, 255, 255, 60))

        elif entity.entity_type == EntityType.LOOP:
            for glow_offset in [10, 5]:
                glow_draw.arc(
                    [x - size - glow_offset, y - size - glow_offset, 
                     x + size + glow_offset, y + size + glow_offset],
                    start=0, end=320, fill=(*color, 50), width=6
                )
            draw.arc([x - size, y - size, x + size, y + size], start=0, end=320, fill=(*color, 255), width=5)
            draw.arc([x - size + 8, y - size + 8, x + size - 8, y + size - 8], start=20, end=300, fill=(*color, 180), width=3)

        elif entity.entity_type == EntityType.CONDITIONAL:
            points = [(x, y - size), (x - size, y + size), (x + size, y + size)]
            glow_points = [(x, y - size - 10), (x - size - 10, y + size + 10), (x + size + 10, y + size + 10)]
            glow_draw.polygon(glow_points, fill=(*color, 25))
            draw.polygon(points, fill=(*color, 230))
            inner_size = size * 0.5
            inner_points = [(x, y - inner_size + 5), (x - inner_size + 5, y + inner_size), (x + inner_size - 5, y + inner_size)]
            draw.polygon(inner_points, fill=(*_brighten(color, 1.3), 100))

        if entity.complexity >= 8:
            marker_size = 4
            draw.line([x - marker_size, y, x + marker_size, y], fill=(255, 255, 255, 200), width=2)
            draw.line([x, y - marker_size, x, y + marker_size], fill=(255, 255, 255, 200), width=2)

    blurred_glow = glow_layer.filter(ImageFilter.GaussianBlur(radius=12))
    blurred_connections = connection_layer.filter(ImageFilter.GaussianBlur(radius=3))
    
    final = Image.new("RGBA", (width, height), (*background, 255))
    final = Image.alpha_composite(final, image)
    final = Image.alpha_composite(final, blurred_glow)
    final = Image.alpha_composite(final, blurred_connections)
    
    shape_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    shape_draw = ImageDraw.Draw(shape_layer)
    
    for x, y, entity in all_positions:
        base_size = 20 + (entity.mass // 4)
        size = min(base_size + entity.complexity * 6, 100)
        color = _get_color_for_entity(entity, config)

        if entity.entity_type == EntityType.CLASS:
            half = size // 2
            shape_draw.rectangle([x - half, y - half, x + half, y + half], fill=(*color, 200))
            shape_draw.rectangle([x - half, y - half, x + half, y + half], outline=(255, 255, 255, 120), width=2)

        elif entity.entity_type == EntityType.FUNCTION:
            shape_draw.ellipse([x - size, y - size, x + size, y + size], fill=(*color, 240))
            if entity.complexity > 5:
                inner = size // 3
                shape_draw.ellipse([x - inner, y - inner, x + inner, y + inner], fill=(255, 255, 255, 80))

        elif entity.entity_type == EntityType.LOOP:
            shape_draw.arc([x - size, y - size, x + size, y + size], start=0, end=320, fill=(*color, 255), width=6)
            shape_draw.arc([x - size + 10, y - size + 10, x + size - 10, y + size - 10], start=30, end=290, fill=(*color, 200), width=3)

        elif entity.entity_type == EntityType.CONDITIONAL:
            points = [(x, y - size), (x - size, y + size), (x + size, y + size)]
            shape_draw.polygon(points, fill=(*color, 240))
            inner_size = size * 0.4
            inner_points = [(x, y - inner_size + 8), (x - inner_size + 8, y + inner_size), (x + inner_size - 8, y + inner_size)]
            shape_draw.polygon(inner_points, fill=(*_brighten(color, 1.4), 120))

        if entity.complexity >= 8:
            marker_size = 5
            shape_draw.line([x - marker_size, y, x + marker_size, y], fill=(255, 255, 255, 220), width=2)
            shape_draw.line([x, y - marker_size, x, y + marker_size], fill=(255, 255, 255, 220), width=2)

    final = Image.alpha_composite(final, shape_layer)
    final.convert("RGB").save(output_path, "PNG")
