from doomdark_game_data_tools import *
from doomdark_map_tools import *

files = [
        "day1.sna",
        "day2_landrintunnels.sna",
        "day3.sna",
        "day4.sna",
        "day5.sna",
        "day6.sna",
        "day7.sna",
        "day8.sna",
        "day9.sna",
        "day10.sna"]
input_file = os.path.join('./game_snaps_sna2/daily_snaps', files[6])
# mt = MapTools(file_path=input_file)
#map_data = mt.read_map_data()
#mt.draw_map_image(map_data, output_file="./map/png/mymap.png")
#mt.export_map_html(map_data, output_file="./map/html/mymap.html")
cp = GameTableDataExtract()
for dayfile in files :
    dayfile = os.path.join('./game_snaps_sna2', dayfile)
    cp.read_all_characters_location_data(dayfile)
    cp.UpdateTodaysCharacterDataDictionary()
    cp.UpdateDayByDayCharacterData()
    cp.WriteDayDataToSQLiteDatabase()
    # cp.WriteToCSV(filename=dayfile+'.csv')
DailyCharData = cp.ReturnDayByDayCharacterData()

input_file = os.path.join('./game_snaps_sna2', files[0])
mt = MapTools(file_path=input_file)
map_data = mt.read_map_data()
mt.export_map_html(map_data=map_data, output_file="./map/html/mymap.html")
