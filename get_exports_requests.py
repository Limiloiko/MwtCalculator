# get_exports_requests.py

## imports
import sys
import os
import logging
import requests
import keyring
import argparse
from bs4 import BeautifulSoup
from requests.cookies import RequestsCookieJar


class MyCookieJar(RequestsCookieJar):
    #TODO: This is not working as expected!
    def clear_expired(self):
        # do nothing to not remove expired cookies
        pass

    def clear_expired_cookies(self) -> None:
        pass

    def clear_session_cookies(self) -> None:
        pass


SERVICE_NAME = "MWT"

LOGIN_URL = "https://131.gospec.net/webtimevigo/login.php?make=1"
CURRENT_MONTH = "https://131.gospec.net/webtimevigo/mt.php?op=5"

logging.basicConfig(level=logging.NOTSET)


def mwt_login(user):
    """A sample function that processes the input argument."""
    # check if credentials already stored in windows credentials manager

    password = keyring.get_password(SERVICE_NAME, user)

    if not password:
        password = input("Please, write your password:")
        keyring.set_password(SERVICE_NAME, user, password)

    payload = {
        "username": user,
        "password": password
    }
    # Open a session to save cookies and so
    session = requests.Session()
    # set custom class to handle cookies to keep them
    session.cookies = MyCookieJar()
    # Try to connect
    response = session.post(LOGIN_URL, data=payload, allow_redirects=False, verify=False)

    if response.ok:
        print("Login success")
    else:
        sys.exit("Login error!")

    #TODO: This is not working! Cookies not filled!?
    return session


def mwt_export(session, user, year):
    """Function that is responsible of accessing mwt and download each month tics"""

    for month in range(1, 13, 1):
        print("Downloading month: ", month)
        month_id = f"{year}{str(month).zfill(2)}"

        url = f"https://131.gospec.net/webtimevigo/common/diario_pdf.php?opt=2&mes={month_id}&emid={user}"

        headers = {
            "Host": "131.gospec.net",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Connection": "keep-alive",
            "Referer": "https://131.gospec.net/webtimevigo/mt/mov_iframes.php?app=1&op=5",
            "Cookie": f"mywtuser={user}; mywtpass=47rwkQlTxReaA; mywtprv={user}-0-0",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "iframe",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "If-Modified-Since": "Fri, 29 Nov 2024 14:24:54 GMT",
            "Priority": "u=4",
            "TE": "trailers"
        }

        # get response, the server will generate a file to access and download
        response = session.get(url, headers=headers, verify=False)

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

                file_response = session.get(download_url, headers=headers, verify=False)
                if file_response.ok:

                    file_name = os.path.join("downloads", f"{month_id}.txt")
                    with open(file_name, "wb") as file:
                        file.write(file_response.content)
                else:
                    print(f"Error downloading the file {month_id}: {file_response.status_code}")
            else:
                sys.exit("No window open in request response!")
        else:
            sys.exit("Response not ok for xls request!")


def get_script_arguments():
    """Function that processes the input arguments."""
    parser = argparse.ArgumentParser(description="Download MWT exports")
    parser.add_argument("--user", type=str, help="User to login")
    parser.add_argument("--year", type=int, help="Year to download")
    return parser.parse_args()


def main():
    """Main function"""
    # handle input arguments
    args = get_script_arguments()

    # Login to Mwt
    session = mwt_login(args.user)

    # Download this year months, one by one
    mwt_export(session, args.user, args.year)


if __name__ == "__main__":
    main()
