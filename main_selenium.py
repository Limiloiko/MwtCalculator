import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import keyring

SERVICE_NAME = "MWT"
USERNAME = "47528"

LOGIN_URL = "https://131.gospec.net/webtimevigo/login.php"
CURRENT_MONTH = "https://131.gospec.net/webtimevigo/mt.php?op=5"

# Configuración del WebDriver
CHROME_DRIVER_PATH = "ruta/al/chromedriver"  # Cambiar por la ruta de tu ChromeDriver


def mwt_login(driver):
    """Función que realiza el inicio de sesión en la página."""
    # Recuperar o solicitar la contraseña
    password = keyring.get_password(SERVICE_NAME, USERNAME)

    if not password:
        password = input("Please, write your password:")
        keyring.set_password(SERVICE_NAME, USERNAME, password)

    # Navegar a la página de login
    driver.get(LOGIN_URL)

    # Encontrar los campos de usuario y contraseña
    username_field = driver.find_element(By.NAME, "username")
    password_field = driver.find_element(By.NAME, "password")

    # Ingresar credenciales
    username_field.send_keys(USERNAME)
    password_field.send_keys(password)

    # Enviar el formulario (presionando Enter)
    password_field.send_keys(Keys.RETURN)

    # Esperar a que se cargue la página posterior al login
    time.sleep(3)

    # Verificar si el login fue exitoso
    if "dashboard" in driver.current_url.lower():  # Ajusta este criterio según tu página
        print("Login success")
    else:
        sys.exit("Login error! Revisa tus credenciales.")


def mwt_export(driver):
    """Función que descarga el archivo del mes actual desde MWT."""
    month = "11"
    year = "2024"
    month_id = f"{year}{month}"

    # Construir la URL para la descarga
    url = f"https://131.gospec.net/webtimevigo/common/diario_pdf.php?opt=2&mes={month_id}&emid={USERNAME}"

    # Navegar a la URL de descarga
    driver.get(url)

    # Esperar unos segundos para asegurarse de que se descargue
    time.sleep(5)

    print("Archivo descargado. Verifica la carpeta de descargas predeterminada.")


def main():
    """Función principal"""
    # Configurar las opciones de Selenium
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": "C:\\Projects\\MwtCalculator\\downloads",
        "download.prompt_for_download": False,
        "directory_upgrade": True
    })

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        # Iniciar sesión
        mwt_login(driver)

        # Descargar el archivo del mes actual
        mwt_export(driver)

    finally:
        # Cerrar el navegador
        driver.quit()


if __name__ == "__main__":
    main()
