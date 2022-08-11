# this scripts runs through all of teh skattemandtalslister
# and tries to find the different road entities that arent linked to the 
# skattemandtalslister. It then makes a dump of these to update the website



from pathlib import Path

from fuzzywuzzy import fuzz
import csv
import ast
import re
import json
import pdb


def clean_string(string: str) -> str:
    clean_str = re.sub(r"\(|\)|-|," ,"", string)
    clean_str = clean_str.replace(" ", "")
    clean_str = clean_str.lower()
    return clean_str


def get_road_names_by_year() -> dict:
    directory: Path = Path("Skattemandtalslister")
    road_names_by_year: dict = {}
    for skatmand_list in directory.glob('*'):
        with open (skatmand_list, 'r', encoding="utf-8") as skatmand_file:
            year = re.search(r"skattemandtal_\d\d\d\d", str(skatmand_list)).group()
            skatmand_dict: dict = json.load(skatmand_file)
            list_of_skatmand = skatmand_dict.get('result')
            temp_list: list = []
            for skatmand in list_of_skatmand:
                road_name_str: str = skatmand.get('label')
                road_name_list: list = road_name_str.split(",")
                for road in road_name_list:
                    road = road.replace("Skattemandtalslister", "")
                    road = clean_string(road)
                    temp_list.append(road)
            road_names_by_year[year] = temp_list
        skatmand_file.close()
    return road_names_by_year

def get_vejviser_roadnumbers_by_year() -> dict: 
    directory: Path = Path("Kios_gadenavne")
    road_numbers_by_year: dict = {}
    for vejviser in directory.glob('*'):
        with open(vejviser, "r", encoding="utf-8") as vejviser_file:
            

def get_location_entities() -> dict:
    location_entities: dict = {}
    entities_file_path: Path = Path("2019-05-13_entity_backup.csv")
    with open (entities_file_path, 'r', encoding="utf-8", newline="") as entities_file:
        reader = csv.DictReader(entities_file)
        for line in reader:
            if line['domain'] == 'locations':
                id = line['id']
                # the data needs to be reformated a bit to 
                # ensure that we can parse it as a dict and not str
                data = line['data']
                data = data.replace('"', '\\"')
                data = ast.literal_eval(line['data'])
                road_and_number_str = line['display_label']
                # removes year defining when the road is made from the string
                road_and_number_str = re.sub(r"\(\d+.\)", "", road_and_number_str)
                # important that we clean bot instanses of road names the same way, to 
                # ensure the highest propability of a hit 
                road_and_number_str = clean_string(road_and_number_str)
                location_entities[road_and_number_str] = {"data":data, "id":id, "number":"N/A"}
    entities_file.close()
    return location_entities

def main():
    location_entities = get_location_entities()
    road_names_by_year = get_road_names_by_year()
    dict_of_misses: dict[str, list] = {}
    dict_of_hits: dict[str, list] = {}

    years = road_names_by_year.keys()
    misses = 0
    hits = 0
    for year in years:
        roads: list[str] = road_names_by_year[year]
        for road in roads:
            location = location_entities.get(road, 'NOT FOUND IN ' + year)
            if "NOT FOUND" in location:
                list_of_misses: list = dict_of_misses.get(year, None)
                if list_of_misses:
                    list_of_misses.append(road)
                    dict_of_misses[year] = list_of_misses
                else:
                    list_of_misses: list = [road]
                    dict_of_misses[year] = list_of_misses
                misses += 1
            else:
                list_of_hits: list = dict_of_hits.get(year, None)
                if list_of_hits:
                    list_of_hits.append(road)
                    dict_of_hits[year] = list_of_hits
                else:
                    list_of_hits: list = [road]
                    dict_of_hits[year] = list_of_hits
                hits += 1
    
    for year in years:
        i = 0
        j = 0
        hits: list[str] = dict_of_hits[year]
        misses: list[str] = dict_of_misses[year]
        for hit in hits:
            for mis in misses:
                if hit == mis:
                    j = j + 1
                elif fuzz.ratio(hit, mis) >= 85:
                    i = i + 1
        print(year, " had the following stats: ", "near hits: ", i, "true hits: ", j)

if __name__ == "__main__":
    main()
