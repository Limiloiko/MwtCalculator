
# import libraries
import os
import sys
import logging
import warnings
import requests
import keyring
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup


warnings.filterwarnings("ignore")

SERVICE_NAME = "MWT"
LOGIN_URL = "https://131.gospec.net/webtimevigo/login.php?make=1"
CURRENT_MONTH = "https://131.gospec.net/webtimevigo/mt.php?op=5"


def get_script_arguments():
    user = input("Enter your username: ")
    year = input("Enter the year to download: ")

    return user, year


def mwt_login(user):
    """A sample function that processes the input argument."""
    # check if credentials already stored in windows credentials manager

    password = keyring.get_password(SERVICE_NAME, user)

    if not password:
        password = input("Please, write your password:")
        keyring.set_password(SERVICE_NAME, user, password)

    payload = {
        "duser": user,
        "dpass": password
    }
    # Open a session to save cookies and so
    session = requests.Session()

    # Try to connect
    response = session.post(LOGIN_URL, data=payload, allow_redirects=True, verify=False)

    if response.ok:
        # check difference between login success and login error
        # if the set-cookie header is present, then it is a success
        if "set-cookie" in response.headers:
            logging.debug("Login success")
        else:
            # remove stored password
            keyring.delete_password(SERVICE_NAME, user)
            sys.exit("Login error, check your credentials and try again! Remember that MyWebTime maybe has specific \
password, so do not use your windows one!")
    else:
        sys.exit("Login error!")

    return session


def parse_cookies(session):
    for cookie_name, cookie_value in session.cookies.items():
        if cookie_name == "mywtprv":
            cookie_value = cookie_value.split("-")[0]
            logging.debug("Session ID found: %s", cookie_value)
            return cookie_value

    sys.exit("No user_id found in cookies!")


def mwt_export(session, user_id, year):
    """Function that is responsible of accessing mwt and download each month tics"""

    for month in range(1, 13, 1):
        print("Downloading month: ", month)
        month_id = f"{year}{str(month).zfill(2)}"

        url = f"https://131.gospec.net/webtimevigo/common/diario_pdf.php?opt=2&mes={month_id}&emid={user_id}"

        # get response, the server will generate a file to access and download
        response = session.get(url, verify=False)

        if response.ok:
            # parse response to get new url
            soup = BeautifulSoup(response.text, "html.parser")
            script_tag = soup.find("script")

            if script_tag and "window.open" in script_tag.text:
                script_content = script_tag.text.strip()
                start = script_content.find("../")
                end = script_content.find(");")
                relative_url = script_content[start:end].strip('"')

                download_url = os.path.join("https://131.gospec.net/webtimevigo", relative_url.lstrip("../"))

                file_response = session.get(download_url, verify=False)
                if file_response.ok:

                    file_name = os.path.join("downloads", f"{month_id}.txt")
                    # create the folder if it does not exist
                    if not os.path.exists("downloads"):
                        os.makedirs("downloads")

                    with open(file_name, "wb") as file:
                        file.write(file_response.content)
                else:
                    print(f"Error downloading the file {month_id}: {file_response.status_code}")
            else:
                sys.exit("No window open in request response!")
        else:
            sys.exit("Response not ok for xls request!")


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
                logging.debug("Lunes found, incrementing cw number and resetting total hours")
                summary.append({"cw": cw_number, "total": week_hours})
                cw_number += 1
                week_hours = 0

            # calculate hours of the day
            week_hours += calculate_day(line[3], list_line)

    return summary


def calculate_day(day, list_day):
    day_hours = 0

    if "festiva horas extras" in list_day:
        day_hours = 8
    else:

        ticks = list_day[2][:-1].split("|")

        # Special days are taken as E 24:00
        if "24:00" in list_day[2]:
            logging.debug("Found a vacations day: %s!", day)
            day_hours = 8

        elif len(ticks) % 2 != 0:
            # check if future day?
            current_day = datetime.now()
            date = datetime.strptime(day, "%d-%m-%Y")

            if current_day > date:
                logging.warning(f"Error in day {day}! missing ticks?!")
            day_hours = 8
        else:
            for pair in range(0, len(ticks), 2):
                start = datetime.strptime(ticks[pair].strip().split(" ")[-1], "%H:%M")
                end = datetime.strptime(ticks[pair+1].strip().split(" ")[-1], "%H:%M")
                diff = (end - start)

                day_hours += diff.total_seconds() / 3600

    return day_hours


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


# main
if __name__ == "__main__":
    # handle optional verbose argument
    if "-v" in sys.argv:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # handle input arguments
    logging.debug("Getting script arguments ...")
    user, year = get_script_arguments()

    # Login to Mwt
    logging.debug("Logging in ...")
    session = mwt_login(user)

    # ger user_id from cookies
    logging.debug("Parsing cookies ...")
    user_id = parse_cookies(session)

    # Download this year months, one by one
    logging.debug("Downloading exports ...")
    mwt_export(session, user_id, year)

    # process exports
    logging.debug("Processing exports ...")
    if not os.path.exists(f"downloads/{year}.txt"):
        merge_reports(year)

    logging.debug("Processing year ...")
    summary = process_year(f"downloads/{year}.txt")

    logging.debug("Creating html ...")
    create_html(summary)

    logging.debug("Remove stored files ...")

    # remove stored files
    for file in os.listdir("downloads"):
        if file.endswith(".txt"):
            os.remove(os.path.join("downloads", file))
    os.removedirs("downloads")

    # sum all hours
    logging.debug("Calculating balance ...")
    total_hours = 0
    # do not take 0 as valid cw
    for cw in summary[1:]:
        total_hours += (cw["total"] - 40)

    print("Hours balance:", total_hours)
    input("Press enter to exit ...")
