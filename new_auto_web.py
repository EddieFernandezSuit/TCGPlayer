from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium import webdriver
import subprocess
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
# example
# commands = [
#     ['go', BECU_URL],
#     ['fill', USER_ID_INPUT_XPATH, user_id],
#     ['fill', PASSWORD_INPUT_XPATH, password],
#     ['click', LOGIN_BUTTON_XPATH],
#     ['click', CREDIT_CARD_ACCOUNT_XPATH],
#     ['select', DOWNLOAD_TYPE_DROPDOWN_XPATH, 3],
#     ['click', DOWNLOAD_BUTTON_XPATH],
#     ['wait', 20],
# ]

class NewAutoWeb(webdriver.Chrome):
    def __init__(self, commands=None, options: Options = None, service: Service = None, keep_alive: bool = True) -> None:
        options = Options()
        subprocess.Popen('"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\selenum\ChromeProfile"', shell=True)
        options.add_experimental_option("debuggerAddress", "localhost:9222")
        options.add_argument("--disable-notifications")
        super().__init__(options, service, keep_alive)
        self.wait_time = 5
        if commands:
            self.execute_commands(commands)

    def find(self, identifier, type=By.XPATH):
        return WebDriverWait(self, self.wait_time).until(EC.presence_of_element_located((type, identifier)))
    
    def finds(self, identifier, type=By.XPATH):
        return WebDriverWait(self, self.wait_time).until(EC.presence_of_all_elements_located((type, identifier)))
    
    def click(self, identifier="", type=By.XPATH):
        self.sleep(1)
        WebDriverWait(self, self.wait_time).until(EC.element_to_be_clickable((type, identifier))).click()
    
    def click_many(self, xpaths):
            for xpath in xpaths:
                self.click(xpath)
    
    def fill(self, identifier, input_string, type=By.XPATH):
        self.sleep(1)
        self.find(identifier, type).send_keys(input_string)

    def select(self, identifier, value, type=By.XPATH):
        dropdown_menu = self.find(identifier, type)
        select = Select(dropdown_menu)
        select.select_by_value(value)
    
    def new_tab(self):
        self.switch_to.new_window('tab')
    
    def clear(self, identifier, type=By.XPATH):
        self.find(identifier).clear()
    
    def wait(self):
        input('Press Enter')
    
    def sleep(self, t=2):
        time.sleep(2)

    def execute_commands(self, commands):
        for command in commands:
            action = command[0]
            args = command[1:] if len(command) > 1 else []

            if hasattr(self, action):
                getattr(self, action)(*args)
            else:
                raise ValueError(f"Invalid action: {action}")