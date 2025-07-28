import csv
import sqlite3

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
        self.TodaysCharacterData = []
        self.DayByDayCharacterData = []
        self.Day = 1

    def UpdateTodaysCharacterDataDictionary(self, limitIdx=128, ) :

        idx = 0

        self.TodaysCharacterData = []
        
        while(idx < 128) :
            thisCharacter = {}

            thisCharacter['ID'] = idx
            thisCharacter['Day'] = self.Day

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
            
            thisCharacter['Pros'] = self.GetPositiveAttributes(idx)
            thisCharacter['Cons'] = self.GetNegativeAttributes(idx)

            self.TodaysCharacterData.append(thisCharacter)
            idx += 1
        
        pass
        # pprint.pprint(self.characterData[5], compact=True)

    def UpdateDayByDayCharacterData(self):
        self.DayByDayCharacterData.append(self.TodaysCharacterData)
        self.Day += 1

    def ReturnDayByDayCharacterData(self):
        return self.DayByDayCharacterData

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
                "CharFlags2_race",
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

    def WriteDayDataToSQLiteDatabase(self, sqlliteDatabaseName='sqllite.db') :
        conn = sqlite3.connect(sqlliteDatabaseName)
        cursor = conn.cursor()

        # Create unified table with flattened flags
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS characters (
                id INTEGER,
                day INTEGER,
                name TEXT,
                race TEXT,
                full_title TEXT,
                current_x INTEGER,
                current_y INTEGER,
                home_x INTEGER,
                home_y INTEGER,
                army_size INTEGER,
                foe TEXT,
                liege TEXT,
                energy INTEGER,
                despondency INTEGER,
                recklessness INTEGER,
                state TEXT,
                killed_battle_128 BOOLEAN,
                lost_battle_128 BOOLEAN,
                army_size_128 INTEGER,
                fortress_owner_128 TEXT,
                flags1_LookDirection TEXT,
                flags1_TimeOfDay INTEGER,
                flags2_race TEXT,
                flags2_orders INTEGER,
                flags3_InBattle BOOLEAN,
                flags3_InTunnel BOOLEAN,
                flags3_KilledFoe BOOLEAN,
                flags3_Loyalty TEXT,
                flags3_UsedObject BOOLEAN,
                flags3_WonBattle BOOLEAN,
                PRIMARY KEY(id, day)
            )
        ''')

        for c in self.TodaysCharacterData :
            # Flatten nested flags into top-level fields
            c['flags1_LookDirection'] = c['CharFlags1'].get('LookDirection', None)
            c['flags1_TimeOfDay']     = c['CharFlags1'].get('TimeOfDay', None)
            c['flags2_race']          = c['CharFlags2'].get('race', None)
            c['flags2_orders']        = c['CharFlags2'].get('orders', None)
            c['flags3_InBattle']      = c['CharFlags3'].get('InBattle', None)
            c['flags3_InTunnel']      = c['CharFlags3'].get('InTunnel', None)
            c['flags3_KilledFoe']     = c['CharFlags3'].get('KilledFoe', None)
            c['flags3_Loyalty']       = c['CharFlags3'].get('Loyalty', None)
            c['flags3_UsedObject']    = c['CharFlags3'].get('UsedObject', None)
            c['flags3_WonBattle']     = c['CharFlags3'].get('WonBattle', None)

            cursor.execute('''
                INSERT OR IGNORE INTO characters VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                c['ID'],
                c['Day'],
                c['Name'],
                c['Race'],
                c['FullTitle'],
                c['CurrentCoords']['x'],
                c['CurrentCoords']['y'],
                c['HomeCoords']['x'],
                c['HomeCoords']['y'],
                c['ArmySize'],
                c['Foe'],
                c['Liege'],
                c['Energy'],
                c['Despondency'],
                c['Recklessness'],
                c['State'],
                c['KilledBattle128'],
                c['LostBattle128'],
                c['ArmySize128'],
                c['FortressOwner128'],
                c['flags1_LookDirection'],
                c['flags1_TimeOfDay'],
                c['flags2_race'],
                c['flags2_orders'],
                c['flags3_InBattle'],
                c['flags3_InTunnel'],
                c['flags3_KilledFoe'],
                c['flags3_Loyalty'],
                c['flags3_UsedObject'],
                c['flags3_WonBattle']
            ))

        conn.commit()
        conn.close()

    def WriteToCSV(self, filename="chars.csv") :

        # Flatten each dictionary
        flattened = [self.flatten_dict(char) for char in self.TodaysCharacterData]

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
