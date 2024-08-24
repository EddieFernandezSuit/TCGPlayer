from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
import subprocess

class AutoWeb():
    def __init__(self, isLocal=False):
        options = Options()
        if isLocal:
            subprocess.Popen('"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\selenum\ChromeProfile"', shell=True)
            options.add_experimental_option("debuggerAddress", "localhost:9222")
        options.add_argument("--disable-notifications")
        self.driver = webdriver.Chrome(options=options)
        self.driver.maximize_window()
        self.wait_time = 10
        
    def find_element(self, type, identifier):
        return WebDriverWait(self.driver, self.wait_time).until(EC.presence_of_element_located((type, identifier)))
    
    def find_elements(self, type, identifier):
        return WebDriverWait(self.driver, self.wait_time).until(EC.presence_of_all_elements_located((type, identifier)))
    
    def go(self, url):
        self.driver.get(url)
    
    def quit(self):
        self.driver.quit()

    def click(self, type, identifier):
        WebDriverWait(self.driver, self.wait_time).until(EC.element_to_be_clickable((type, identifier))).click()
    
    def click_many(self, xpaths):
        for xpath in xpaths:
            self.click(By.XPATH, xpath)
    
    def fill(self, type, identifier, input_string):
        self.find_element(type, identifier).send_keys(input_string)
    
    def select(self, type, identifier, index):
        dropdown_menu = self.find_element(type, identifier)
        select = Select(dropdown_menu)
        select.select_by_index(index)
    
    def new_tab(self):
        self.driver.switch_to.new_window('tab')