from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from new_auto_web import NewAutoWeb
from selenium.webdriver.common.keys import Keys
import time
from config import *
from config import *
import pyautogui

class Tcg_web(NewAutoWeb):
    def __init__(self, commands=None, isOption=True):
        super().__init__(commands, isOption)
        self.handle_tcg_login()
        self.PRICING_URL = "https://store.tcgplayer.com/admin/pricing"

    def handle_tcg_login(self):
        ACCOUNT_BUTTON_COORDS = (680,550)
        NEWT_TAB_BUTTON_COORDS = (340,30)
        TCG_SHORTCUT_COORDS = (1100,120)
        SIGN_IN_BUTTON_COORDS = (960,600)
        pyautogui.click(ACCOUNT_BUTTON_COORDS)
        time.sleep(2)
        pyautogui.click(NEWT_TAB_BUTTON_COORDS)
        pyautogui.click(TCG_SHORTCUT_COORDS)
        time.sleep(3)
        pyautogui.click(SIGN_IN_BUTTON_COORDS)
        time.sleep(10)
        self.switch_to.window(self.window_handles[-1])

    def set_items_per_page(self, num_item_per_page):
        OLD_ITEMS_PER_PAGE = '//*[@id="table-page-counts"]/span[2]/select'
        # ROWS_PER_PAGE_XPATH = '//*[@id="tcg-input-198"]'
        items_per_page = self.find(OLD_ITEMS_PER_PAGE)
        Select(items_per_page).select_by_value(str(num_item_per_page))

    def download_pricing(self):
        PRICING_BUTTON_XPATH = '//*[@id="pricing-search"]/pricing-search/div[4]/pricing-actions/div[1]/div[1]/div/input[1]'
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
                self.download_pricing()
                time.sleep(1)
                self.click(IMPORT_TO_STAGED_XPATH)
                file_input = self.find(UPLOAD_XPATH)
                file_input.send_keys(prices_file_path)
                self.click(CONTINUE_XPATH)
                self.click(CONTINUE_XPATH2) 
                self.click(MOVE_TO_LIVE_XPATH)
                self.click(COMFIRM_MOVE_TO_LIVE_XPATH)
                self.click(CLOSE_XPATH)
                # auto_web.switch_to.window(auto_web.window_handles[-1])
                # auto_web.close()
                # auto_web.quit()
                cont = False
            except Exception as e:
                print(e)
                input('Error Press Enter to Contrinue')


def download_files_normal():
    while True:
        try:
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
            # READY_TO_SHIP_BUTTON = '//*[@id="OrderIndex_QuickFilters_RadioReadytoShip"]'
            # MARK_AS_SHIPPED_BUTTON = '//*[@id="single-spa-application:@tcgplayer/sellerportal-orders"]/div[1]/div[1]/div[1]/div[1]/div[4]/div[1]/div[1]/div[2]/div[1]/div[1]/div[1]/button[3]/span[2]'
            # EXPORT_SHIPPING_BUTTON = '//*[@id="single-spa-application:@tcgplayer/sellerportal-orders"]/div[1]/div[1]/div[1]/div[1]/div[4]/div[1]/div[1]/div[2]/div[1]/div[1]/div[1]/button[2]/span[2]'
            # PACKING_SLIP_XPATH = '//*[@id="single-spa-application:@tcgplayer/sellerportal-orders"]/div/div/div/div/div[4]/div/div/div[2]/div/div/div[1]/div[2]/div/button'
            # PACKING_SLIP_XPATH2 = '/html/body/div[7]/div[26]/div/div/div[2]/button[1]'
            CHANGE_UI_XPATH = '//*[@id="tcg-input-12"]'

            tcg_web = Tcg_web()
            number_of_orders = int(input("Enter number of orders: "))
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
        except Exception as e:
            print(e)
            input('Error, Press enter to try again')

def download_files_direct():
    auto_web = Tcg_web()
    auto_web.download_pricing()
    auto_web.go("https://store.tcgplayer.com/admin/ro")
    auto_web.click(identifier="/html/body/div[4]/div/div[6]/div[2]/table/tbody/tr[1]/td[1]/a")
    auto_web.click(identifier='//*[@id="btnPackingSlip"]')
    auto_web.click(identifier='//*[@id="btnPackingSlipCSV"]')
    auto_web.quit()

