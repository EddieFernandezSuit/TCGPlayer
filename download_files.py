from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from auto_web import AutoWeb
import time
from config import *

def download_tcgplayer_files():
    auto_web = AutoWeb(isLocal=True)
    # auto_web.new_tab()
    # auto_web.go("")
    # input('Press Enter To Continue')
    # auto_web.go("https://store.tcgplayer.com/admin/Seller/Dashboard/4c622486")
    input('Press Enter To Continue')
    auto_web.driver.switch_to.window(auto_web.driver.window_handles[-1])
    auto_web.go("https://store.tcgplayer.com/admin/pricing")
    auto_web.click(By.XPATH, '//*[@id="pricing-search"]/pricing-search/div[4]/pricing-actions/div[1]/div[1]/div/input[1]')
    auto_web.go("https://store.tcgplayer.com/admin/orders/orderlist")
    number_of_orders_to_show = auto_web.find_element(By.XPATH, '//*[@id="table-page-counts"]/span[2]/select')
    Select(number_of_orders_to_show).select_by_value("100")
    auto_web.click(By.XPATH, '//*[@id="rightSide"]/div/div[4]/div/div[2]/div[1]/div[2]/div[2]/div[2]/button')
    time.sleep(2)
    auto_web.click(By.XPATH, '//*[@id="rightSide"]/div/div[4]/div/span/div/div[3]/div/div[2]/table/thead/tr/th[1]/div/span[1]/div/label/span[1]')
    auto_web.click(By.XPATH, '//*[@id="search-results-buttons"]/button[1]')
    auto_web.click(By.XPATH, '//*[@id="search-results-buttons"]/button[2]')
    auto_web.click(By.XPATH, '/html/body/div[4]/div/div[4]/div/span/div/div[2]/div/div[1]/div[1]/button')
    auto_web.find_element(By.XPATH, '//*[@id="search-results-buttons"]/div[1]/div[3]/div/a[1]').click()
    auto_web.quit()

def upload_tcgplayer_prices(file_path):
    auto_web = AutoWeb(isLocal=True)
    input('Press Enter To Continue')
    auto_web.driver.switch_to.window(auto_web.driver.window_handles[-1])
    auto_web.go("https://store.tcgplayer.com/admin/pricing")
    auto_web.click(By.XPATH, '/html/body/div[4]/div/div[4]/div[2]/pricing-search/div[4]/pricing-actions/div[1]/div[1]/div/input[4]')
    file_input = auto_web.find_element(By.XPATH, '/html/body/div[4]/div/div[6]/pricing-dialog/div/div/div[2]/pricing-importer/div/div/div[1]/input')
    # file_input.send_keys(PROJECT_DIRECTORY + file_path)
    file_input.send_keys(file_path)
    auto_web.click(By.XPATH, '/html/body/div[4]/div/div[6]/pricing-dialog/div/div/div[2]/pricing-importer/div/div/div[2]/input')
    auto_web.click(By.XPATH, '/html/body/div[4]/div/div[6]/pricing-dialog/div/div/div[2]/pricing-importer/div/div/div/input[2]')  # continue button
    auto_web.click(By.XPATH, '/html/body/div[4]/div/div[6]/pricing-dialog/div/div/div[2]/pricing-importer/div/div/div/input[3]')  # move to live button
    auto_web.click(By.XPATH, '/html/body/div[4]/div/div[6]/pricing-dialog/div/div/div[2]/pricing-move-to-live/div/div/div/input[2]')  # confirm move to live button
    auto_web.click(By.XPATH, '/html/body/div[4]/div/div[6]/pricing-dialog/div/div/div[2]/pricing-move-to-live/div/div/div[2]/input')  # close button
    auto_web.quit()