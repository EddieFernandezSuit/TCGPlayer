from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from auto_web import AutoWeb
import time
from config import *

class TCGPlayer(AutoWeb):
    def handle_tcg_login(self):
        input('Press Enter after logging in to TCGPlayer To Continue')
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def set_items_per_page(self, items):
        number_of_orders_to_show = self.find_element(By.XPATH, '//*[@id="table-page-counts"]/span[2]/select')
        Select(number_of_orders_to_show).select_by_value(str(items))

    def download_pricing(self):
        self.go("https://store.tcgplayer.com/admin/pricing")
        self.click(By.XPATH, '//*[@id="pricing-search"]/pricing-search/div[4]/pricing-actions/div[1]/div[1]/div/input[1]')

    def click_pullsheet(self):
        self.click(identifier='//*[@id="search-results-buttons"]/button[1]')

    def click_all_results(self):
        self.click(By.XPATH, '//*[@id="rightSide"]/div/div[4]/div/span/div/div[3]/div/div[2]/table/thead/tr/th[1]/div/span[1]/div/label/span[1]')

def download_pricing():
    tcg = TCGPlayer(isLocal=True)
    tcg.handle_tcg_login()
    tcg.download_pricing()
    time.sleep(2)
    return tcg

def upload_prices(auto_web: AutoWeb, prices_file_path):
    auto_web.go("https://store.tcgplayer.com/admin/pricing")
    auto_web.click(By.XPATH, '/html/body/div[4]/div/div[4]/div[2]/pricing-search/div[4]/pricing-actions/div[1]/div[1]/div/input[4]')
    file_input = auto_web.find_element(By.XPATH, '/html/body/div[4]/div/div[6]/pricing-dialog/div/div/div[2]/pricing-importer/div/div/div[1]/input')
    file_input.send_keys(prices_file_path)
    auto_web.click(By.XPATH, '/html/body/div[4]/div/div[6]/pricing-dialog/div/div/div[2]/pricing-importer/div/div/div[2]/input')
    auto_web.click(By.XPATH, '/html/body/div[4]/div/div[6]/pricing-dialog/div/div/div[2]/pricing-importer/div/div/div/input[2]')  # continue button
    auto_web.click(By.XPATH, '/html/body/div[4]/div/div[6]/pricing-dialog/div/div/div[2]/pricing-importer/div/div/div/input[3]')  # move to live button
    auto_web.click(By.XPATH, '/html/body/div[4]/div/div[6]/pricing-dialog/div/div/div[2]/pricing-move-to-live/div/div/div/input[2]')  # confirm move to live button
    auto_web.click(By.XPATH, '/html/body/div[4]/div/div[6]/pricing-dialog/div/div/div[2]/pricing-move-to-live/div/div/div[2]/input')  # close button
    auto_web.quit()

def download_files_normal():
    auto_web = TCGPlayer(isLocal=True)
    auto_web.handle_tcg_login()
    auto_web.download_pricing()
    auto_web.go("https://store.tcgplayer.com/admin/orders/orderlist")
    auto_web.set_items_per_page(500)
    auto_web.click(By.XPATH, '//*[@id="rightSide"]/div/div[4]/div/div[2]/div[1]/div[2]/div[2]/div[2]/button')
    time.sleep(2)
    auto_web.click_all_results()
    auto_web.click_pullsheet()
    auto_web.click(By.XPATH, '//*[@id="search-results-buttons"]/button[2]')
    auto_web.click(By.XPATH, '/html/body/div[4]/div/div[4]/div/span/div/div[2]/div/div[1]/div[1]/button')
    auto_web.find_element(By.XPATH, '//*[@id="search-results-buttons"]/div[1]/div[3]/div/a[1]').click()
    auto_web.quit()

def download_files_direct():
    auto_web = TCGPlayer(isLocal=True)
    auto_web.handle_tcg_login()
    auto_web.download_pricing()
    auto_web.go("https://store.tcgplayer.com/admin/ro")
    auto_web.click(identifier="/html/body/div[4]/div/div[6]/div[2]/table/tbody/tr[1]/td[1]/a")
    auto_web.click(identifier='//*[@id="btnPackingSlip"]')
    auto_web.click(identifier="/html/body/div[4]/div/div[5]/ul/li/a")
    auto_web.set_items_per_page(500)
    time.sleep(2)
    auto_web.click_all_results()
    auto_web.click_pullsheet()
    auto_web.quit()


def upload_tcgplayer_prices(file_path):
    auto_web = AutoWeb(isLocal=True)
    input('Press Enter To Continue')
    auto_web.driver.switch_to.window(auto_web.driver.window_handles[-1])
    upload_prices(auto_web, file_path)
