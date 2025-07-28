from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
import pprint
import json

MAP_WIDTH = 64
MAP_HEIGHT = 96
TILE_SIZE = 64 # pixels
MAP_SIZE = MAP_WIDTH * MAP_HEIGHT

class MapTools :

    def __init__(self, file_path='', base_address=0x4000, skip_bytes=27) :
        self.make_terrain_data() 
        self.file_path = file_path
        self.base_address = base_address
        self.skip_bytes = skip_bytes
        self.movement_data = {}
    #-------------------------------------------------------------------
    #
    #   Set up the terrain colours and graphics table
    #
    #-------------------------------------------------------------------
    def make_terrain_data(self) :
        self.terrain = {
            0: ((245, 245, 230), None),             # Plain (no graphic, use solid fill only)
            1: ((101, 67, 33), "mountain.gif"),     # Mountain
            2: ((34, 139, 34), "forest.gif"),       # Forest
            3: ((210, 180, 140), "hills.gif"),      # Hills
            4: ((255, 182, 193), "gate.gif"),       # Gate
            5: ((255, 105, 180), "temple.gif"),     # Temple
            6: ((0, 0, 0), "pit.gif"),              # Pit
            7: ((255, 20, 147), "palace.gif"),      # Palace
            8: ((250, 0, 0), "fortress.gif"),       # Fortress
            9: ((255, 248, 220), "hall.gif"),       # Hall
            10: ((255, 250, 205), "hut.gif"),        # Hut
            11: ((255, 255, 153), "tower.gif"),     # Tower
            12: ((255, 0, 0), "city.gif"),          # City
            13: ((0, 0, 240), "fountain.gif"),      # Fountain
            14: ((255, 255, 204), "stones.gif"),    # Stones
            15: ((173, 216, 230), "icywaste.gif"),  # Ice
        }

    #-------------------------------------------------------------------
    #
    #   Read the map data. If from a sna or whatever, it can have offsets
    #   so if we look for a sequence, we can find it this way. 
    #
    #   If we are not looking from a SNA, the data lives at 0xA800
    #-------------------------------------------------------------------
    def read_map_data(self):
        sequence = bytes([0x2C, 0x0F, 0x0F, 0x0F, 0x01])
        with open(self.file_path, 'rb') as f:
            data = f.read()
        offset = data.find(sequence)
        if offset != -1 :
            sna_adjusted_offset = offset + self.base_address - self.skip_bytes # SNA has 27 bytes at start then starts at address 0x4000
            print(f'Found sequence at offset 0x{sna_adjusted_offset:04X}')
            chunk = data[offset : offset + 6144]
            return chunk
        else : 
            print(f'Did not find sequence')
            return -1

    #-------------------------------------------------------------------
    #
    #   Draw the map as a PNG using the graphics and colours in the
    #   terrain table.
    #
    #-------------------------------------------------------------------
    def draw_map_image(self, map_data, output_file='map.png'):
        print(f"Creating map as PNG : {output_file}")
        
        try:
            os.makedirs('./map/png', exist_ok=True)
        except:
            print('Cannot create png map folder')
            exit(1)

        img_width = MAP_WIDTH * TILE_SIZE
        img_height = MAP_HEIGHT * TILE_SIZE
        image = Image.new('RGBA', (img_width, img_height), color=(0, 0, 0, 255))
        draw = ImageDraw.Draw(image)

        # Preload terrain graphics
        tile_images = {}
        for terrain_id, (color, filename) in self.terrain.items():
            if filename:
                path = os.path.join("graphics", filename)
                try:
                    tile = Image.open(path).convert("RGBA").resize((TILE_SIZE, TILE_SIZE))
                    # tile.show()
                    tile_images[terrain_id] = tile
                except Exception as e:
                    print(f"Failed to load '{filename}' for terrain ID {terrain_id}: {e}")

        for row in range(MAP_HEIGHT):
            for col in range(MAP_WIDTH):
                index = row * MAP_WIDTH + col
                terrain_id = map_data[index] & 0xF
                color, filename = self.terrain.get(terrain_id, ((255, 0, 0), None))
                x = col * TILE_SIZE
                y = row * TILE_SIZE

                # Draw solid color first
                draw.rectangle([x, y, x + TILE_SIZE, y + TILE_SIZE], fill=color)

                # Overlay graphic if it exists
                tile = tile_images.get(terrain_id)
                if tile:
                    image.paste(tile, (x, y), tile)

        image.save(output_file)
        print(f"Map saved to {output_file}")

    #-------------------------------------------------------------------
    #
    #   Draw the map as a HTML using the graphics and colours in the
    #   terrain table.
    #
    #   This could support tunnels but I've turned it off.
    #
    #-------------------------------------------------------------------
    def add_movement_overlay_js(self):
        return '''
    <script>
    fetch("movements.json")
    .then(response => response.json())
    .then(data => {
        const map = document.getElementById("map");
        for (const [day, movements] of Object.entries(data)) {
        movements.forEach(({ name, path }, index) => {
            const color = ['red', 'blue', 'green', 'orange', 'purple', 'gold'][index % 6];
            path.forEach(([x, y]) => {
            const tile = map.querySelector(`[data-x='${x}'][data-y='${y}']`);
            if (tile) {
                tile.style.outline = `3px solid ${color}`;
                tile.style.outlineOffset = "-3px";
                tile.title += `\\n${name}, ${day}`;
            }
            });
        });
        }
    });
    </script>
    '''

    #-------------------------------------------------------------------
    #
    #   Draw the map as a HTML using the graphics and colours in the
    #   terrain table.
    #
    #   This could support tunnels but I've turned it off.
    #
    #-------------------------------------------------------------------
    def export_map_html(self, map_data, output_file='map.html'):
        print(f"Creating map as HTML : {output_file}")
        try:
            os.makedirs('./map/html', exist_ok=True)
        except:
            print('Cannot create HTML map folder')
            exit(1)
        tile_size = TILE_SIZE  # For consistency
        width = MAP_WIDTH
        height = MAP_HEIGHT

        # Preload terrain styles
        terrain_styles = {}
        for terrain_id, (color, filename) in self.terrain.items():
            r, g, b = color
            style = f"background-color: rgb({r},{g},{b});"
            if filename:
                # path = os.path.join("graphics", filename)
                path = os.path.relpath(os.path.join("graphics", filename), os.path.dirname(output_file))
                # Use relative path so browser can load it
                # style += f" background-image: url('{path}'); background-size: cover; background-position: center;"
                style += (
                    f" background-image: url('{path}'); "
                    "background-size: 100% 100%; background-repeat: no-repeat; background-position: center;"
                )
            terrain_styles[terrain_id] = style

        # Start building HTML
        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "  <meta charset='UTF-8'>",
            "  <title>Map Viewer</title>",
            "  <style>",
            f"    #map {{ display: grid; grid-template-columns: repeat({width}, {tile_size}px); grid-auto-rows: {tile_size}px; }}",
            f"    .tile {{ width: {tile_size}px; height: {tile_size}px; border: 1px solid #333; box-sizing: border-box; }}",
            "    #tooltip { position: absolute; background: rgba(0,0,0,0.7); color: #fff; padding: 4px 6px; font-size: 12px; pointer-events: none; display: none; border-radius: 4px; z-index: 100; }",
            "  </style>",
            "</head>",
            "<body>",
            "  <div id='map'>"
        ]

        for row in range(height):
            for col in range(width):
                index = row * width + col
                
                terrain_id = map_data[index] & 0xF
                #is_tunnel = map_data[index] & 0x80

                #if is_tunnel:
                #    style = "background-color: rgb(30,144,255);"  # DodgerBlue for tunnels
                #else:
                #    style = terrain_styles.get(terrain_id, "background-color: red;")
                style = terrain_styles.get(terrain_id, "background-color: red;")
                html.append(
                    f"<div class='tile' style=\"{style}\" data-x='{col}' data-y='{row}' "
                    "onmouseover='showTooltip(event, this)' onmouseout='hideTooltip()'></div>"
                )

        html.extend([
            "  </div>",
            "  <div id='tooltip'>X: --, Y: --</div>",
            "  <script>",
            "    const tooltip = document.getElementById('tooltip');",
            "    function showTooltip(e, tile) {",
            "      const x = tile.dataset.x;",
            "      const y = tile.dataset.y;",
            "      tooltip.textContent = `X: ${x}, Y: ${y}`;",
            "      tooltip.style.left = e.pageX + 10 + 'px';",
            "      tooltip.style.top = e.pageY + 10 + 'px';",
            "      tooltip.style.display = 'block';",
            "    }",
            "    function hideTooltip() {",
            "      tooltip.style.display = 'none';",
            "    }",
            "  </script>"])
        html.append(self.add_movement_overlay_js())
        html.append("</body>")
        html.append("</html>")

        Path(output_file).write_text("\n".join(html))
        print(f"Map saved to {output_file}")

    #-------------------------------------------------------------------
    #
    #   Format character movement data for JSON
    #
    #-------------------------------------------------------------------
    def Format_movements_for_json(self, daily_data):
        movements = {}
        for day_index, entries in enumerate(daily_data, start=1):
            day_key = f"Day {day_index}"
            movements[day_key] = []
            for entry in entries:
                name = entry.get("Name")
                coords = entry.get("CurrentCoords", {})
                movements[day_key].append({
                    "name": name,
                    "path": [[coords.get("x"), coords.get("y")]]
                })
        return movements

    #-------------------------------------------------------------------
    #
    #   Export data to JSON
    #
    #-------------------------------------------------------------------
    def ExportMovementDataToJSON(self, daily_data) :
        Path('map/html/movements.json').write_text(json.dumps(self.Format_movements_for_json(daily_data)))



