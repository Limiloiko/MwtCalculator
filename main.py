# Main script

## imports
import sys
import os
import logging
import requests
import keyring
from bs4 import BeautifulSoup
from requests.cookies import RequestsCookieJar

class MyCookieJar(RequestsCookieJar):
    def clear_expired(self):
        # do nothing to not remove expired cookies
        pass
    def clear_expired_cookies(self) -> None:
        pass
    def clear_session_cookies(self) -> None:
        pass

SERVICE_NAME = "MWT"
USERNAME = "47528"

LOGIN_URL = "https://131.gospec.net/webtimevigo/login.php?make=1"
CURRENT_MONTH = "https://131.gospec.net/webtimevigo/mt.php?op=5"

def get_cookies(cookie_jar, domain):
    cookie_dict = cookie_jar.get_dict(domain=domain)
    found = ['%s=%s' % (name, value) for (name, value) in cookie_dict.items()]
    return ';'.join(found)

logging.basicConfig(level=logging.NOTSET)

def mwt_login():
    """A sample function that processes the input argument."""
    # check if credentials already stored in windows credentials manager

    password = keyring.get_password(SERVICE_NAME, USERNAME)

    if not password:
        password = input("Please, write your password:")
        keyring.set_password(SERVICE_NAME, USERNAME, password)

    payload = {
        "username": USERNAME,
        "password": password
    }
    # Open a session to save cookies and so
    session = requests.Session()
    # set custom class to handle cookies to keep them
    session.cookies = MyCookieJar()
    # Try to connect
    response = session.post(LOGIN_URL, data=payload, allow_redirects=False)

    if response.ok:
        print("Login success")
    else:
        sys.exit("Login error!")

    #TODO: This is not working!
    return get_cookies(response.cookies, "gospec.net")


def mwt_export():
    """Function that is responsible of accessing mwt and download each month tics"""

    month = "11"
    year = "2024"

    for month in range(1, 13, 1):
        print("Downloading month: ", month)
        month_id = f"{year}{str(month).zfill(2)}"

        url = f"https://131.gospec.net/webtimevigo/common/diario_pdf.php?opt=2&mes={month_id}&emid={USERNAME}"

        headers = {
            "Host": "131.gospec.net",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Connection": "keep-alive",
            "Referer": "https://131.gospec.net/webtimevigo/mt/mov_iframes.php?app=1&op=5",
            "Cookie": "mywtuser=47528; mywtpass=47rwkQlTxReaA; mywtprv=47528-0-0",
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
        response = requests.get(url, headers=headers)

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

                file_response = requests.get(download_url, headers=headers)
                if file_response.ok:

                    file_name = os.path.join("downloads", f"{month_id}.xls")
                    with open(file_name, "wb") as file:
                        file.write(file_response.content)
                else:
                    print(f"Error downloading the file {month_id}: {file_response.status_code}")
            else:
                sys.exit("No window open in request response!")
        else:
            sys.exit("Response not ok for xls request!")


def main():
    """Main function"""
    ### Login to Mwt
    cookies = mwt_login()

    ### Download this year months, one by one
    mwt_export(cookies)

    ### process each export and calculate things

if __name__ == "__main__":
    main()
