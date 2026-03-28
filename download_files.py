from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from new_auto_web import NewAutoWeb
from selenium.webdriver.common.keys import Keys
from constants import *
import time
import pyautogui

def rewrite(coords: tuple, text: str):
    pyautogui.click(coords) 
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('backspace')
    pyautogui.write(text)

class Tcg_web(NewAutoWeb):
    def __init__(self, commands=None, isOption=True, email:str=EMAIL):
        super().__init__(commands, isOption)
        self.email = email
        self.password = PASSWORD
        self.PRICING_URL = "https://store.tcgplayer.com/admin/pricing"
        self.handle_tcg_login()

    def handle_tcg_login(self):
        EMAIL_COORDS = pyautogui.Point(952,413)
        PASSWORD_COORDS = pyautogui.Point(1141,523)
        LOGIN_PAGE_BUTTON_COORDS = (500, 570)
        LOGIN_BUTTON_COORDS = (960, 590)

        time.sleep(1)
        pyautogui.click(LOGIN_PAGE_BUTTON_COORDS)
        time.sleep(1)
        pyautogui.click(EMAIL_COORDS)
        rewrite(EMAIL_COORDS, self.email)
        rewrite(PASSWORD_COORDS, self.password)
        pyautogui.click(LOGIN_BUTTON_COORDS)
        time.sleep(1)
        # self.switch_to.window(self.window_handles[-1])

    def set_items_per_page(self, num_item_per_page):
        OLD_ITEMS_PER_PAGE = '//*[@id="table-page-counts"]/span[2]/select'
        items_per_page = self.find(OLD_ITEMS_PER_PAGE)
        Select(items_per_page).select_by_value(str(num_item_per_page))

    def download_pricing(self):
        PRICING_BUTTON_XPATH = '//*[@id="pricing-search"]/pricing-search/div[4]/pricing-actions/div[1]/div[1]/div/input[1]'
        time.sleep(2)
        self.get(self.PRICING_URL)
        time.sleep(1)
        self.click(PRICING_BUTTON_XPATH)
        time.sleep(2)

    def upload_prices(self, prices_file_path):
        CONTINUE_XPATH = '//*[@id="divImportButtonContainer"]/input'
        CONTINUE_XPATH2 = '//*[@id="divImporterUploadContainer"]/div/input[2]'
        IMPORT_TO_STAGED_XPATH = '//*[@id="pricing-search"]/pricing-search/div[4]/pricing-actions/div[1]/div[1]/div/input[4]'
        UPLOAD_XPATH = '//*[@id="divImporterUploadContainer"]/div[1]/input'
        MOVE_TO_LIVE_XPATH = '//*[@id="divImporterUploadContainer"]/div/input[3]'
        COMFIRM_MOVE_TO_LIVE_XPATH = '//*[@id="pricing-dialog"]/pricing-dialog/div/div/div[2]/pricing-move-to-live/div/div/div/input[2]'
        CLOSE_XPATH = '//*[@id="pricing-dialog"]/pricing-dialog/div/div/div[2]/pricing-move-to-live/div/div/div[2]/input'
        cont = True
        while cont:
            try:    
                self.go(self.PRICING_URL)
                # self.download_pricing()
                time.sleep(1)
                self.click(IMPORT_TO_STAGED_XPATH)
                file_input = self.find(UPLOAD_XPATH)
                file_input.send_keys(prices_file_path)
                self.click(CONTINUE_XPATH)
                self.click(CONTINUE_XPATH2) 
                self.click(MOVE_TO_LIVE_XPATH)
                self.click(COMFIRM_MOVE_TO_LIVE_XPATH)
                self.click(CLOSE_XPATH)
                cont = False
            except Exception as e:
                print(e)
                input('Error Press Enter to Contrinue')


def download_files_normal(download_pricing:bool=True, email:str=''):
    URL = "https://store.tcgplayer.com/admin/orders/orderlist"
    OLD_UI = {
        'READY_TO_SHIP':'//*[@id="rightSide"]/div/div[4]/div/div[2]/div[1]/div[2]/div[2]/div[2]/button',
        'ALL_ORDERS':'//*[@id="rightSide"]/div/div[4]/div/span/div/div[3]/div/div[2]/table/thead/tr/th[1]/div/span[1]/div/label/span[1]',
        'PULL_SHEET':'//*[@id="search-results-buttons"]/button[1]',
        'PACKING_SLIP1':'//*[@id="search-results-buttons"]/div[1]/div[1]/button',
        'PACKING_SLIP2':'//*[@id="search-results-buttons"]/div[1]/div[3]/div/a[1]',
        'EXPORT_SHIPPING':'//*[@id="search-results-buttons"]/button[2]',
        'MARK_AS_SHIPPED':'//*[@id="search-results-buttons"]/button[4]'

    }
    CHANGE_UI_XPATH = '//*[@id="tcg-input-12"]'

    tcg_web = Tcg_web(email=email)
    number_of_orders = int(input("Enter number of orders: "))
    if download_pricing:
        tcg_web.download_pricing()
    tcg_web.go(URL)
    tcg_web.click(CHANGE_UI_XPATH)
    tcg_web.set_items_per_page(100)
    time.sleep(2)
    tcg_web.click(OLD_UI['READY_TO_SHIP'])
    time.sleep(2)
    tcg_web.click(OLD_UI['ALL_ORDERS'])
    tcg_web.click(OLD_UI['PULL_SHEET'])
    tcg_web.click(OLD_UI['PACKING_SLIP1'])
    tcg_web.click(OLD_UI['PACKING_SLIP2'])
    tcg_web.click(OLD_UI['EXPORT_SHIPPING'])
    tcg_web.click(OLD_UI['MARK_AS_SHIPPED'])
    tcg_web.sleep(3)
    tcg_web.quit()
    return number_of_orders

def download_files_direct():
    auto_web = Tcg_web()
    auto_web.download_pricing()
    auto_web.go("https://store.tcgplayer.com/admin/ro")
    auto_web.click(identifier="/html/body/div[4]/div/div[6]/div[2]/table/tbody/tr[1]/td[1]/a")
    auto_web.click(identifier='//*[@id="btnPackingSlip"]')
    auto_web.click(identifier='//*[@id="btnPackingSlipCSV"]')
    auto_web.quit()

