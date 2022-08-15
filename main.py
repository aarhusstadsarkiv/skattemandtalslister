# this scripts runs through all of the skattemandtalslister
# and tries to find the different road entities that arent linked to the 
# skattemandtalslister. It then makes a dump of these to update the website



from doctest import OutputChecker
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
    # some roads havde their construction year in parentheses like so:
    # test vej 43D (1967-). This is interesting info, and might be usefull in 
    # later versions, but rn we just remove it.
    clean_str = re.sub(r"\(\d+.\)", "", string)
    clean_str = re.sub(r"\(|\)|-|," ,"", clean_str)
    clean_str = clean_str.replace(" ", "")
    clean_str = clean_str.lower()
    return clean_str

# removes everything but the digits from a string
# and returns an int
def clean_number(string: Union[str, None]) -> int:
    string = str(string)
    if string is None:
        return None
    clean_str = re.sub(r"[\D\s]+", "", string)
    if not clean_str:
        return None
    return int(clean_str)


def get_skatmand_road_names_by_year() -> dict:
    directory: Path = Path("Skattemandtalslister")
    road_names_by_year: dict = {}
    for skatmand_list in directory.glob('*'):
        with open (skatmand_list, 'r', encoding="utf-8") as skatmand_file:
            year = re.search(r"skattemandtal_\d\d\d\d", str(skatmand_list)).group()
            skatmand_dict: dict = json.load(skatmand_file)
            list_of_skatmand = skatmand_dict.get('result')
            list_of_roads: list = []
            temp_dict: dict[str, list] = {}
            for skatmand in list_of_skatmand:
                id = skatmand.get('id')
                road_name_str: str = skatmand.get('label')
                road_name_list: list = road_name_str.split(",")
                for road in road_name_list:
                    road = road.replace("Skattemandtalslister", "")
                    road = clean_road_name(road)
                    if road not in list_of_roads:
                        list_of_roads.append(road)
                        temp_dict[id] = road
                    else:
                        print('fuck')
            year = re.search(r"\d\d\d\d", year).group()
            road_names_by_year[year] = temp_dict
        skatmand_file.close()
    return road_names_by_year

# the values passed to the function can also be None
# TODO see if this makes sense to make excplicit in mypy
def make_list_of_addresses(road_name: str,
                                even_start: int, 
                                even_end: int, 
                                uneven_start: int, 
                                uneven_end: int) -> list:
    result: list[str] = []

    if even_start is not None and even_end is not None:
        for i in range(even_start, even_end + 2, 2):
            temp_str = road_name + str(i)
            result.append(temp_str)
    elif even_start is not None and even_end is None:
        temp_str = road_name + str(even_start)
        result.append(temp_str)
    elif even_start is None and even_end is not None:
        temp_str = road_name + str(even_end)
        result.append(temp_str)
    
    if uneven_start is not None and uneven_end is not None:
        for i in range(uneven_start, uneven_end + 2, 2):
            temp_str = road_name + str(i)
            result.append(temp_str)
    elif uneven_start is not None and uneven_end is None:
        temp_str = road_name + str(uneven_start)
        result.append(temp_str)
    elif uneven_start is None and uneven_end is not None:
        temp_str = road_name + str(uneven_end)
        result.append(temp_str)

    return result

# contains both the info from vejviseren and a list of all addresses based on this info
def get_road_info_by_year() -> dict: 
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
            # vejviseren at a time. If this isnt the case, prints a warning.
            if i == 0:
                i += 1
                continue
            i += 1
            year: int = row[0]
            if year_check is not None and year is not None:
                if year != year_check:
                    warnings.warn('Warning: Data not as excpected. See road_info_by_year function for explaination')
                    warnings.warn('Warning: discrepancy found in ' + str(vejviser) + " row " + str(i) + " with data " + str(row))
                    warnings.warn('Year variable was: ' + str(year) + " year_check was: " + str(year_check))
            
            # cleaning as all other road names to ensure uniformity
            road_name: str = clean_road_name(str(row[1]))
            uneven_start: int = clean_number(row[2])
            uneven_end: int = clean_number(row[3])
            even_start: int = clean_number(row[4])
            even_end: int = clean_number(row[5])
            list_of_addresses = make_list_of_addresses(road_name, even_start, even_end, uneven_start, uneven_end)
    
            # bad naming, TODO: give better names
            temp_dict_2: dict[str, Union[str, list, int]] = {'year':year, 'uneven_start':uneven_start, 'uneven_end':uneven_end, 'even_start':even_start, 'even_end':even_end, 'list_of_addresses': list_of_addresses}
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
    skatmand_roads_by_year: dict[str, list] = get_skatmand_road_names_by_year()
    road_info_by_year: dict[str, dict] = get_road_info_by_year()
    location_entities_by_road_and_number: dict[str, dict] = get_location_entities()
    result: dict = {}

    years: list[str] = skatmand_roads_by_year.keys()
    list_of_missed_addresses: list = []
    total_list_of_addresses: list = []
    missing_addresses = 0
    total_addresses = 0
    for year in years:
        skatmand_roads_by_id: dict = skatmand_roads_by_year[year]

        # if the year isnt represented in the road info dict, continue to next year
        try:
            road_info: dict = road_info_by_year[year]
        except (KeyError):
            continue

        for skatmand_id in skatmand_roads_by_id.keys():
            road: str = skatmand_roads_by_id[skatmand_id]
            # if the road is not represented in the current year, continue
            try:
                road_info_dict = road_info[road]
            except (KeyError):
                continue
            list_of_addresses = road_info_dict['list_of_addresses']
            temp_list: list = []
            # if the address isnt represented in the location entity set, add it to
            # the list of missed addresses and continue
            for address in list_of_addresses:
                try:
                    location_entity_dict = location_entities_by_road_and_number[address]
                    temp_list.append(location_entity_dict['id'])
                    total_list_of_addresses.append(address)
                    total_addresses += 1
                except (KeyError):
                    missing_addresses += 1
                    total_addresses += 1
                    list_of_missed_addresses.append(address)
                    total_list_of_addresses.append(address)
                    continue
            try:
                result_list = result[skatmand_id]
                temp_list.append(result_list)
                result[skatmand_id] = temp_list
            except (KeyError):
                result[skatmand_id] = temp_list

    json_file = json.dumps(result)
    output = open('output.json', 'w')
    output.write(json_file)
    output.close()
    
    missed_list = open("misses.txt", "w", encoding='utf-16')
    for address in list_of_missed_addresses:
        missed_list.write(f"{address}\n")
    missed_list.close()

    print("We missed this many addresses:", missing_addresses, "out of", total_addresses)

if __name__ == "__main__":
    main()
