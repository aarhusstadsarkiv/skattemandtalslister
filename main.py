# this scripts runs through all of teh skattemandtalslister
# and tries to find the different road entities that arent linked to the 
# skattemandtalslister. It then makes a dump of these to update the website


from pathlib import Path

import json
import pdb


directory: Path = Path("Skattemandtalslister")
for skatmand_list in directory.glob('*'):
    with open (skatmand_list, 'r') as sktamand_file:
        skatmand_dict: dict = json.load(sktamand_file)
        list_of_skatmand = skatmand_dict.get('result')
        for skatmand in list_of_skatmand:
            name: str = skatmand.get('label')
            name_list: list = name.split(",")
            test: list = []
            for road in name_list:
                road = road.replace("Skattemandtalslister", "")
                road = road.replace(",", "")
                road = road.replace(" ", "")
                test.append(road)
            print(test)
