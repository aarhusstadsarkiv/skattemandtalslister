# This script fixes the remaining roads from the
# skattemandtalslister provided by Kio
# Specifications: Connect the given skatmanID with
# road IDs by looking into the entity list
import json
from pathlib import Path
import openpyxl

from main import clean_road_name2, get_location_entities_by_road_name


location_entities_by_road_and_addresses: dict[
    str, dict
] = get_location_entities_by_road_name()


def get_list_of_ids_to_skatmand(
    start: int, end: int, road_name: str
) -> list[str]:
    """
    Iterates over all the numbers from start until end,
    and appends them to road_name to make an address
    If the address has an ID in the entity-set, this is found
    and added to the result
    Returns all addresses_ID's in the range.
    """
    result: list[str] = []
    if not start or not end:
        return result
    for i in range(start, end + 1, 2):
        address: str = road_name + str(i)
        address_data = location_entities_by_road_and_addresses.get(address)
        # We can have a situation where there is no data
        if not address_data:
            continue
        address_id = address_data.get("id")
        if address_id:
            result.append(address_id)
    return result


def main() -> None:
    path_to_file: Path = Path(r"Kios_gadenavne\duplicate_roads_by_year.xlsx")
    # We have to make the string 'raw' (r) in ordrer to avoid W605 warnings
    wb_temp: openpyxl.Workbook = openpyxl.load_workbook(path_to_file)
    sheet: openpyxl.Worksheet = wb_temp.active
    # i is used to keep track of index in worksheet
    # We iterate over the first ID
    i: int = 0
    skatmand_id_to_list_of_address_id: dict[int, list] = {}
    for row in sheet.iter_rows(values_only=True):
        # Skip the first row, only contains headers
        if i == 0:
            i += 1
            continue
        i += 1
        skatmand_id_1: int = row[0]
        skatmand_id_2: int = row[1]

        skatmand_id_to_list_of_address_id[skatmand_id_1]: list[str] = []
        skatmand_id_to_list_of_address_id[skatmand_id_2]: list[str] = []

        road_name: str = clean_road_name2(str(row[2]))

        first_even_start: int = row[3]
        first_even_end: int = row[4]
        first_odd_start: int = row[5]
        first_odd_end: int = row[6]

        second_even_start: int = row[7]
        second_even_end: int = row[8]
        second_odd_start: int = row[9]
        second_odd_end: int = row[10]

        # The method for finding the address id's for a road
        # is here made as a helper method
        skatmand_id_to_list_of_address_id[skatmand_id_1].append(
            get_list_of_ids_to_skatmand(
                first_even_start, first_even_end, road_name
            )
        )
        skatmand_id_to_list_of_address_id[skatmand_id_1].append(
            get_list_of_ids_to_skatmand(
                first_odd_start, first_odd_end, road_name
            )
        )

        # And for the other skatmand
        skatmand_id_to_list_of_address_id[skatmand_id_2].append(
            get_list_of_ids_to_skatmand(
                second_even_start, second_even_end, road_name
            )
        )
        skatmand_id_to_list_of_address_id[skatmand_id_2].append(
            get_list_of_ids_to_skatmand(
                second_odd_start, second_odd_end, road_name
            )
        )

    json_file: str = json.dumps(skatmand_id_to_list_of_address_id)
    output = open("missing_addresses.json", "w")
    output.write(json_file)
    output.close()


if __name__ == "__main__":
    main()
