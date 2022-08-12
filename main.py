# this scripts runs through all of teh skattemandtalslister
# and tries to find the different road entities that arent linked to the 
# skattemandtalslister. It then makes a dump of these to update the website



from pathlib import Path
from typing import Union
import warnings
from fuzzywuzzy import fuzz

import openpyxl
import csv
import ast
import re
import json
import pdb

# used to clean roadnames to ensure the formatiing is the same across files
# does not correct spelling or anything like that
def clean_road_name(string: str) -> str:
    # some roads havde their construction year in parentheses like soo:
    # test vej 43D (1967-). This is interesting info, and might be usefull in 
    # later versions, but rn we just remove it.
    clean_str = re.sub(r"\(\d+.\)", "", string)
    clean_str = re.sub(r"\(|\)|-|," ,"", clean_str)
    clean_str = clean_str.replace(" ", "")
    clean_str = clean_str.lower()
    return clean_str


def get_skatmand_road_names_by_year() -> dict:
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
                    road = clean_road_name(road)
                    temp_list.append(road)
            year = re.search(r"\d\d\d\d", year).group()
            road_names_by_year[year] = temp_list
        skatmand_file.close()
    return road_names_by_year

def get_vejviser_road_info_by_year() -> dict: 
    directory: Path = Path("Kios_gadenavne")
    road_numbers_by_year: dict[str, dict] = {}
    for vejviser in directory.glob('*.xlsx'):
        wb_temp = openpyxl.load_workbook(filename=vejviser)
        sheet = wb_temp.active
        year_check: int = None
        temp_dict_1: dict = {}
        # i is used to keep track of index in worksheet
        i = 0
        for row in sheet.iter_rows(values_only=True):
            # sanity check: as far as i can see, the different workbooks only have data for one year of
            # the vejviser at a time. If this isnt the case, prints a warning.
            if i == 0:
                i += 1
                continue
            i += 1
            year: int = row[0]
            if year_check is not None and year is not None:
                if year != year_check:
                    warnings.warn('Warning: Data not as excpected. See get_vejviser_road_info_by_year function for explaination')
                    warnings.warn('Warning: discrepancy found in ' + str(vejviser) + " row " + str(i) + " with data " + str(row))
                    warnings.warn('Year variable was: ' + str(year) + " year_check was: " + str(year_check))
            
            # cleaning as all other road names to ensure uniformity
            road_name: str = clean_road_name(str(row[1]))
            # we need to intepret the road numbers as strings, since they can contain letters
            # at the end.
            uneven_start: str = row[2]
            uneven_end: str = row[3]
            even_start: str = row[4]
            even_end: str = row[5]
            # bad naming, TODO: give better names
            temp_dict_2: dict[str, Union[str, int]] = {'year':year, 'uneven_start':uneven_start, 'uneven_end':uneven_end, 'even_start':even_start, 'even_end':even_end}
            temp_dict_1[road_name] = temp_dict_2
            year_check = year
        road_numbers_by_year[str(year)] = temp_dict_1
    return road_numbers_by_year
        
            

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
                # important that we clean both instances of road names the same way, to 
                # ensure the highest propability of a hit.
                road_and_number_str = clean_road_name(road_and_number_str)
                number_list: list = re.findall(r'(\d+\w?)', road_and_number_str)
                try:
                    number: str = number_list[0]
                except (IndexError):
                    number = None
                location_entities[road_and_number_str] = {"data":data, "id":id, "number":number}
    entities_file.close()
    return location_entities

def calculate_simular_roadnames_by_year() -> None:
    location_entities: dict = get_location_entities()
    road_names_by_year: dict = get_skatmand_road_names_by_year()
    dict_of_misses: dict[str, list] = {}
    dict_of_hits: dict[str, list] = {}

    years: list[str] = road_names_by_year.keys()
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

def main():
    location_entities_by_road_and_number: dict[str, dict] = get_location_entities()
    skatmand_road_names_by_year: dict[str, list] = get_skatmand_road_names_by_year()
    vejviser_roadnumber_by_year: dict[str, dict] = get_vejviser_road_info_by_year()

    years: list[str] = skatmand_road_names_by_year.keys()
    print(years)
    print(vejviser_roadnumber_by_year.keys())
    i = 0
    for year in years:
        list_of_roads_skatmand: list = skatmand_road_names_by_year[year]
        dict_of_vejviser_info: dict = vejviser_roadnumber_by_year.get(year, None)
        if dict_of_vejviser_info is not None:
            for road in list_of_roads_skatmand:
                try:
                    road_info = dict_of_vejviser_info[road]
                except (KeyError):
                    i += 1
                    continue
            even_start = road_info['even_start']
            even_end = road_info['even_end']
            uneven_start = road_info['uneven_start']
            uneven_end = road_info['uneven_end']
            if even_start is not None and even_end is not None:
                

    print("We missed ", i, " many roads")
    pdb.set_trace()




if __name__ == "__main__":
    main()
