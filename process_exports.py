# get_exports_requests.py

## imports
import sys
import os
import logging
import argparse
import pandas as pd
from datetime import datetime


logger = logging.getLogger(__file__)


def merge_reports(year):
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
    with open(os.path.join("downloads", f"{year}.txt"), "w") as f:
        f.writelines(merged_file)


def calculate_day(day, list_day):
    day_hours = 0

    if "festiva horas extras" in list_day:
        day_hours = 8
    else:

        ticks = list_day[2][:-1].split("|")

        # Special days are taken as E 24:00
        if "24:00" in list_day[2]:
            logger.debug("Found a vacations day!")
            day_hours = 8

        elif len(ticks) % 2 != 0:
            # check if future day?
            current_day = datetime.now()
            date = datetime.strptime(day, "%d-%m-%Y")

            if current_day > date:
                logger.error(f"Error in day {day}! missing ticks?!")
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

            # do not consider weekends
            if "Sa" in list_line or "Do" in list_line:
                continue
            elif "Lu" in list_line:
                logger.debug("Lunes found, incrementing cw number and resetting total hours")
                summary.append({"cw": cw_number, "total": week_hours})
                cw_number += 1
                week_hours = 0

            # calculate hours of the day
            week_hours += calculate_day(line[3], list_line)

    return summary


def create_html(data):
    """Function that is in charge of creating a simple html with the data processed"""

    df = pd.DataFrame(data)
    html_table = df.to_html(index=False)

    with open("reporte.html", "w") as file:
        file.write(f"""
        <html>
            <head>
                <title>Reporte</title>
            </head>
            <body>
                <h1>Reporte de Datos</h1>
                {html_table}
            </body>
        </html>

    """)


def get_script_arguments():
    """Function that processes the input arguments."""
    parser = argparse.ArgumentParser(description="Download MWT exports")
    parser.add_argument("--year", type=int, help="Year to download")
    return parser.parse_args()


def main():
    """Main function"""

    # parse script arguments
    args = get_script_arguments()

    if not os.path.exists(f"downloads/{args.year}.txt"):
        merge_reports(args.year)

    summary = process_year(f"downloads/{args.year}.txt")

    create_html(summary)

    # sum all hours
    total_hours = 0
    # do not take 0 as valid cw
    for cw in summary[1:]:
        total_hours += (cw["total"] - 40)

    print("Balance:", total_hours)


if __name__ == "__main__":
    main()


