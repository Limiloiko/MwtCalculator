# get_exports_requests.py

## imports
import sys
import os
import logging
from datetime import datetime


logger = logging.getLogger(__file__)


def merge_reports():
    """Open all files inside download and create one single file with all year reports"""

    merged_file = []

    for file in os.listdir("downloads"):
        if file.endswith(".txt"):

            with open(os.path.join("downloads", file), "r") as f:
                contents = f.readlines()
                if "LISTADO DE DETALLE DIARIO" not in contents[0]:
                    sys.exit(f"File {file} is not valid! Exiting!")

                # crop initial lines and last line
                merged_file += contents[4:-1]

    # save merged file
    with open(os.path.join("downloads", "2024.txt"), "w") as f:
        f.writelines(merged_file)


def calculate_day(day, list_day):
    day_hours = 0

    if "festiva horas extras" in list_day:
        day_hours = 0
    else:

        ticks = list_day[2][:-1].split("|")

        if len(ticks) % 2 != 0:
            # maybe day with errors?
            logger.debug(f"Error in one day! missing ticks! {day}")
            day_hours = 8
        else:
            for pair in range(0, len(ticks), 2):
                inicio = datetime.strptime(ticks[pair].strip().split(" ")[-1], "%H:%M")
                fin = datetime.strptime(ticks[pair+1].strip().split(" ")[-1], "%H:%M")
                diff = (fin - inicio)

                day_hours += diff.total_seconds() / 3600

    return day_hours


def process_year(txt_file):
    """Routine that opens and process a given file, returns the summary in dict format"""

    summary = []
    cw_number = 0
    week_hours = 0

    with open(txt_file, "r+") as f:
        year_content = f.readlines()

        for line in year_content:
            line = line.split("\t")
            list_line = line[4:-4]

            if "Sa" in list_line or "Do" in list_line:
                continue
            elif "Lu" in list_line:
                logger.debug("Lunes found, incrementing cw number and reseting total hours")
                summary.append({"cw": cw_number, "total": week_hours})
                cw_number += 1
                week_hours = 0

            # calculate hours of the day
            week_hours += calculate_day(line[3], list_line)

    return summary


def main():
    """Main function"""
    # merge_reports()
    summary = process_year("downloads/2024.txt")
    import pprint as pp
    pp.pprint(summary)


if __name__ == "__main__":
    main()


