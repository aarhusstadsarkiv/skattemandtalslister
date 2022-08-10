import json

start_year = "1925"
end_year = "1929"


def main():
    with open(f"skattemandtal_{start_year}-{end_year}_full.json") as ifile:
        data = json.load(ifile)
        year = start_year
        streets = []
        for el in data.get("result"):
            cur_year = el.get("date_from")[0:4]

            if not cur_year == year:
                # write file with current data
                with open(f"Skattemandtal_{year}_gadenavne.txt", "w") as ofile:
                    for sub_el in sorted(streets):
                        ofile.write(sub_el + "\n")
                # reset data
                year = cur_year
                streets = []

            label = el.get("label").replace("Skattemandtalslister ", "")
            for street in label.split(","):
                if street.strip() not in streets:
                    streets.append(street.strip())

        with open(f"Skattemandtal_{year}_gadenavne.txt", "w") as ofile:
            for el in sorted(streets):
                ofile.write(el + "\n")


if __name__ == "__main__":
    main()
