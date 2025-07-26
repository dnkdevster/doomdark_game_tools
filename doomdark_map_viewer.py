from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
import pprint
import csv


MAP_WIDTH = 64
MAP_HEIGHT = 96
TILE_SIZE = 64 # pixels
MAP_SIZE = MAP_WIDTH * MAP_HEIGHT

class MapTools :

    def __init__(self, file_path, base_address=0x4000, skip_bytes=27) :
        self.make_terrain_data() 
        self.file_path = file_path
        self.base_address = base_address
        self.skip_bytes = skip_bytes

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
            "  </script>",
            "</body>",
            "</html>"
        ])

        Path(output_file).write_text("\n".join(html))
        print(f"Map saved to {output_file}")

class GameTableDataExtract :

    def __init__(self, characterName=None, base_address=0x4000, skip_bytes=27) :
        self.main_chars = ['Luxor', 'Morkin', 'Tarithel', 'Rorthron', 'Shareth']
        self.races = (
            "Moonprince",
            "Moonprince",
            "Free",
            "Fee",
            "Wise",
            "Wise",
            "Fey",
            "Fey",
            "Barbarian",
            "Barbarian",
            "Icelord",
            "Icelord",
            "Fey",
            "Giant",
            "Heartstealer",
            "Dwarf"
        )

        self.base_address = base_address
        self.skip_bytes = skip_bytes
        self.characterData = []

    def UpdateCharacterDataDictionary(self) :
        idx = 0
        while(idx < 128) :
            thisCharacter = {}
            
            thisCharacter['Name'] = self.get_character_name(idx)
        
            (x, y) = self.GetCharacterPosition(idx)
            thisCharacter['CurrentCoords'] = {'x' : x, 'y' : y}

            (x, y) = self.GetCharacterHomePosition(idx)
            thisCharacter['HomeCoords'] = {'x' : x, 'y' : y}

            race = self.get_character_race(idx)
            thisCharacter['Race'] = race
            thisCharacter['FullTitle'] = thisCharacter['Name'] + ' the ' + thisCharacter['Race']

            army_size = self.getArmySize(idx)
            thisCharacter['ArmySize'] = army_size

            charFlags1 = self.GetCharFlags1(idx)
            thisCharacter['CharFlags1'] = charFlags1

            charFlags2 = self.GetCharFlags2(idx)
            thisCharacter['CharFlags2'] = charFlags2

            charFlags3 = self.GetCharFlags3(idx)
            thisCharacter['CharFlags3'] = charFlags3

            thisCharacter['Foe'] = self.GetCharFoe(idx)
            thisCharacter['Liege'] = self.GetCharLiege(idx)

            thisCharacter['Energy'] = self.GetEnergyLevel(idx)
            thisCharacter['Despondency'] = self.GetDespondencyLevel(idx)

            thisCharacter['Recklessness'] = self.GetRecklessness(idx)
            thisCharacter['State'] = self.GetCharacterState(idx)

            thisCharacter['KilledBattle128'] = self.GetKilledInBattle128(idx)
            thisCharacter['LostBattle128'] = self.GetLostInBattle128(idx)
            thisCharacter['ArmySize128'] = self.GetArmySize128(idx)
            thisCharacter['FortressOwner128'] = self.GetFortressOwner128(idx)
            
            print(thisCharacter.keys())
            # thisCharacter['Pros'] = self.GetPositiveAttributes(idx)
            # thisCharacter['Cons'] = self.GetNegativeAttributes(idx)

            self.characterData.append(thisCharacter)
            idx += 1
        
        pprint.pprint(self.characterData[5], compact=True)

            
    def GetCharIndex(self, characterName) :
        self.charIndex = self.main_chars.index(characterName)

    #-------------------------------------------------------------------
    #
    #   Make the character name. This is derived from the position of 
    #   their "home fortress" which lives at address 0x9C00 (x)
    #   and 0x9C80 (y); Shareth starts at a different location to her  
    #   home fortress. I guess Luxor etc are named from elsewhere.
    #
    #-------------------------------------------------------------------
    def get_character_name(self, index):
        Start = (
                "Img", "Dol", "Lor", "Ush", "Mor", "Tal", "Car", "Ulf", "As", "Tor",
                "Ob", "F", "Gl", "S", "Th", "Gan", "Mal", "Im", "Var", "Hag", 
                "Zar", "Anv", "Ber", "Kah", "Ash")
        
        Middle = ("Ar", "Or", "Ir", "En", "Orth", "Angr", "Igr", "Ash",
                "El", "In", "Ul", "Atr", "Orm", "Udr", "Is", "Ildr")
        
        End = ("Orn", "Il", "Iel", "Im", "Uk", "Ium", "Ia", "Eon",
                  "Ay", "Ak", "Arg", "And", "Ane", "Esh", "Ad", "Un")

        if index > 4 :
            fortress_x = self.location_data[0x9C00-self.base_address+index]
            fortress_y = self.location_data[0x9C80-self.base_address+index]
            name_code = 444 * (( fortress_y * 64 ) + fortress_x ) % 6151
            end_idx     = name_code & 0x000F
            mid_idx     = (name_code & 0x00F0) >> 4
            start_idx   = (name_code & 0x1F00) >> 8
            name = Start[start_idx] + Middle[mid_idx].lower() + End[end_idx].lower()
        else:
            name = self.main_chars[index]
        return name

    def GetCharacterPosition(self, characterIndex) :
        x = self.location_data[0xA100-  self.base_address + characterIndex]
        y = self.location_data[0xA180 - self.base_address + characterIndex]
        return (x,y)

    def GetCharacterHomePosition(self, characterIndex) :
        x = self.location_data[0x9C00-  self.base_address + characterIndex]
        y = self.location_data[0x9C80 - self.base_address + characterIndex]
        return (x,y)

    def get_character_race(self, index) :
        race_idx = self.location_data[0xA000-self.base_address+index]
        return self.races[race_idx]

    def getArmySize(self, index) :
        army_size = self.location_data[0x9F00 - self.base_address + index] * 5
        return army_size

    def GetCharFlags1(self, index) :
        
        lookDirection = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        
        charFlags1 = {}
        
        flags1 = self.location_data[0xA200 - self.base_address + index]
        
        look_direction = flags1 & 0x7
        time_of_day = flags1 >> 3
        
        charFlags1['LookDirection'] = lookDirection[look_direction]
        
        if time_of_day == 0x1F :
            charFlags1['TimeOfDay'] = 'Dawn'
        elif time_of_day == 0x00 :
            charFlags1['TimeOfDay'] = 'Night'
        else :
            charFlags1['TimeOfDay'] = 0x1F - time_of_day

        return charFlags1

    def GetCharFlags2(self, index) :
        
        charFlags2 = {}
        
        flags2 = self.location_data[0xA280 - self.base_address + index]
        
        race = flags2 & 0x0F
        orders = flags2 & 0xF0 >> 4
        
        charFlags2['race'] = self.races[race]
        charFlags2['orders'] = orders

        return charFlags2

    def GetCharFlags3(self, index) :
        
        charFlags3 = {}
        
        flags3 = self.location_data[0xA300 - self.base_address + index]
        
        Loyalty = flags3 & 0x07
        KilledFoe = Loyalty & 0x08
        InBattle = Loyalty & 0x10
        WonBattle = Loyalty & 0x20
        InTunnel = Loyalty & 0x40
        UsedObject = Loyalty & 0x80
        
        charFlags3['Loyalty'] = self.returnLoyaltyString(Loyalty)
        charFlags3['KilledFoe'] = True if KilledFoe > 0 else False
        charFlags3['InBattle'] = True if InBattle > 0 else False
        charFlags3['WonBattle'] = True if WonBattle > 0 else False
        charFlags3['InTunnel'] = True if InTunnel > 0 else False
        charFlags3['UsedObject'] = True if UsedObject > 0 else False

        return charFlags3

    def GetCharFoe(self, index) :
        foeCharIndex = self.location_data[0xA480 - self.base_address + index]
        if foeCharIndex < 128 :
            name = self.get_character_name(foeCharIndex)
            race = self.get_character_race(foeCharIndex)
            return name + ' the ' + race
        else :
            return '-'

    def GetCharLiege(self, index) :
        liegeCharIndex = self.location_data[0xA500 - self.base_address + index]
        if liegeCharIndex < 128 :
            name = self.get_character_name(liegeCharIndex)
            race = self.get_character_race(liegeCharIndex)
            return name + ' the ' + race
        else :
            return '-'

    def GetEnergyLevel(self, index) :
        return self.location_data[0xA380 - self.base_address + index]
    
    def GetDespondencyLevel(self, index) :
        return self.location_data[0xA780 - self.base_address + index]

    def GetRecklessness(self, index) :
        return self.location_data[0xA580 - self.base_address + index]

    def GetCharacterState(self, index) :
        recklessness = self.location_data[0xA580 - self.base_address + index]
        return 'Dead' if recklessness == 0 else 'Alive'

    def GetPositiveAttributes(self, index) :
        
        PositiveAttributes = {}
        
        flags = self.location_data[0xA680 - self.base_address + index]

        PositiveAttributes['Good']      = True if flags & 0x01 else False
        PositiveAttributes['Strong']    = True if flags & 0x02 else False
        PositiveAttributes['Forceful']  = True if flags & 0x04 else False
        PositiveAttributes['Generous']  = True if flags & 0x08 else False
        PositiveAttributes['Stubborn']  = True if flags & 0x10 else False
        PositiveAttributes['Brave']     = True if flags & 0x20 else False
        PositiveAttributes['Swift']     = True if flags & 0x40 else False
        PositiveAttributes['Loyal']     = True if flags & 0x80 else False

        return PositiveAttributes

    def GetNegativeAttributes(self, index) :
        
        NegativeAttributes = {}
        
        flags = self.location_data[0xA700 - self.base_address + index]

        NegativeAttributes['Evil']          = True if flags & 0x01 else False
        NegativeAttributes['Weak']          = True if flags & 0x02 else False
        NegativeAttributes['Reticent']      = True if flags & 0x04 else False
        NegativeAttributes['Greedy']        = True if flags & 0x08 else False
        NegativeAttributes['Fawning']       = True if flags & 0x10 else False
        NegativeAttributes['Cowardly']      = True if flags & 0x20 else False
        NegativeAttributes['Slow']          = True if flags & 0x40 else False
        NegativeAttributes['Treacherous']   = True if flags & 0x80 else False

        return NegativeAttributes

    def GetFortressOwner128(self, index) :
        return self.location_data[0xA080 - self.base_address + index]

    def GetKilledInBattle128(self, index) :
        return self.location_data[0x9E00 - self.base_address + index] * 5

    def GetLostInBattle128(self, index) :
        return self.location_data[0x9E80 - self.base_address + index] * 5

    def GetArmySize128(self, index) :
        return self.location_data[0x9F80 - self.base_address + index] * 5

    def ReturnCSVFields(self):
        return ["FullTitle", 
                "CurrentCoords_x", "CurrentCoords_y",
                "ArmySize",
                "HomeCoords_x", "HomeCoords_y",
                "State",
                "Energy",
                "Despondency",
                "Recklessness",
                "Liege",
                "Foe",
                "KilledBattle128",
                "LostBattle128",
                "ArmySize128",
                "FortressOwner128",
                "CharFlags1_LookDirection",
                "CharFlags1_TimeOfDay",
                "CharFlags2_orders",
                "CharFlags3_InBattle",
                "CharFlags3_InTunnel",
                "CharFlags3_KilledFoe",
                "CharFlags3_Loyalty",
                "CharFlags3_UsedObject",
                "CharFlags3_WonBattle"
        ]

    def returnLoyaltyString(self, loyalty) :
        loyalty_table = ['Moonprince', 'Heartstealer', 'Fey', 'Barbarians', 'Giants', 'Dwarfs']
        return loyalty_table[loyalty]

    def read_all_characters_location_data(self, file_path):
        with open(file_path, 'rb') as f:
            data = f.read()[self.skip_bytes:]
        # You can now treat `data[offset]` as memory at address `base_address + offset`
        self.location_data = data

    def report_race_stats(self):        
        try :
            pprint.pprint(self.racestats)
        except:
            print('Error - No Race Stats Generated Yet')

    def flatten_dict(self, d, parent_key="", sep="_"):
        items = {}
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.update(self.flatten_dict(v, new_key, sep=sep))
            else:
                items[new_key] = v
        return items

    def WriteToCSV(self, filename="chars.csv") :

        # Flatten each dictionary
        flattened = [self.flatten_dict(char) for char in self.characterData]

        # Collect all unique fieldnames
        fieldnames = set()
        for entry in flattened:
            fieldnames.update(entry.keys())
        fieldnames = sorted(fieldnames)

        # Write to CSV
        with open(filename, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=self.ReturnCSVFields(), extrasaction='ignore')
            writer.writeheader()
            writer.writerows(flattened)

files = ["doomdarks_day1.sna", "doomdarks_day2.sna", "doomdarks_day3.sna", "doomdarks_day4.sna", "doomdarks_day5.sna", "doomdarks_day6.sna", "doomdarks_day7.sna"]
input_file = os.path.join('./game_snaps_sna/daily_snaps', files[6])
mt = MapTools(file_path=input_file)
#map_data = mt.read_map_data()gt
#mt.draw_map_image(map_data, output_file="./map/png/mymap.png")
#mt.export_map_html(map_data, output_file="./map/html/mymap.html")

cp = GameTableDataExtract()
cp.read_all_characters_location_data(input_file)
cp.UpdateCharacterDataDictionary()
cp.WriteToCSV()
exit(0)

for dayfile in files :
    dayfile = os.path.join('./game_snaps_sna/daily_snaps', dayfile)
    cp.read_all_characters_location_data(dayfile)


'''
Example output

$ python3 doomdark_map_viewer.py 
Character Rorthron is at location x: 5, y: 91
Character Rorthron is at location x: 7, y: 88
Character Rorthron is at location x: 7, y: 88
Character Rorthron is at location x: 7, y: 88
Character Rorthron is at location x: 7, y: 88
Character Rorthron is at location x: 7, y: 88
Character Rorthron is at location x: 5, y: 92
Error - No Race Stats Generated Yet

$ python3 doomdark_map_viewer.py 
Character Luxor is at location x: 5, y: 91
Character Luxor is at location x: 5, y: 91
Character Luxor is at location x: 5, y: 91
Character Luxor is at location x: 5, y: 91
Character Luxor is at location x: 5, y: 91
Character Luxor is at location x: 5, y: 91
Character Luxor is at location x: 5, y: 92
Error - No Race Stats Generated Yet

$ python3 doomdark_map_viewer.py 
Character Shareth is at location x: 56, y: 8
Character Shareth is at location x: 51, y: 13
Character Shareth is at location x: 47, y: 17
Character Shareth is at location x: 47, y: 17
Character Shareth is at location x: 47, y: 24
Character Shareth is at location x: 47, y: 26
Character Shareth is at location x: 47, y: 26
Error - No Race Stats Generated Yet

'''