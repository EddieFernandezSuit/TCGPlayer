from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from new_auto_web import NewAutoWeb
from selenium.webdriver.common.keys import Keys
import time
from config import *
from config import *

class Tcg_web(NewAutoWeb):
    def __init__(self, commands=None, isOption=True):
        super().__init__(commands, isOption)
        self.handle_tcg_login()

    def handle_tcg_login(self):
        input('Press Enter after logging in to TCGPlayer To Continue')
        self.switch_to.window(self.window_handles[-1])

    def set_items_per_page(self, num_item_per_page):
        OLD_ITEMS_PER_PAGE = '//*[@id="table-page-counts"]/span[2]/select'
        # ROWS_PER_PAGE_XPATH = '//*[@id="tcg-input-198"]'
        items_per_page = self.find(OLD_ITEMS_PER_PAGE)
        Select(items_per_page).select_by_value(str(num_item_per_page))

    def download_pricing(self):
        PRICING_BUTTON_XPATH = '//*[@id="pricing-search"]/pricing-search/div[4]/pricing-actions/div[1]/div[1]/div/input[1]'
        self.go("https://store.tcgplayer.com/admin/pricing")
        self.click(PRICING_BUTTON_XPATH)

    def click_pullsheet(self):
        PULLSHEET_BUTTON = '//*[@id="single-spa-application:@tcgplayer/sellerportal-orders"]/div[1]/div[1]/div[1]/div[1]/div[4]/div[1]/div[1]/div[2]/div[1]/div[1]/div[1]/button[1]/span[2]'
        self.click(identifier=PULLSHEET_BUTTON)

    def click_all_results(self):
        ALL_RESULTS_BUTTON = '//*[@id="single-spa-application:@tcgplayer/sellerportal-orders"]/div[1]/div[1]/div[1]/div[1]/div[4]/div[1]/div[1]/div[2]/table[1]/thead[1]/tr[1]/th[1]/div[1]/label[1]/span[1]/span[1]'
        self.click( ALL_RESULTS_BUTTON)

def download_pricing():
    # tcg = Tcg_web(isLocal=True)
    tcg = Tcg_web()
    tcg.download_pricing()
    time.sleep(2)
    return tcg

def upload_prices(auto_web: NewAutoWeb, prices_file_path):
    CONTINUE_XPATH = '//*[@id="divImportButtonContainer"]/input'
    CONTINUE_XPATH2 = '//*[@id="divImporterUploadContainer"]/div/input[2]'
    cont = True
    while cont:
        try:
            auto_web.go("https://store.tcgplayer.com/admin/pricing")
            time.sleep(1)
            auto_web.click('/html/body/div[4]/div/div[4]/div[2]/pricing-search/div[4]/pricing-actions/div[1]/div[1]/div/input[4]')
            file_input = auto_web.find('/html/body/div[4]/div/div[6]/pricing-dialog/div/div/div[2]/pricing-importer/div/div/div[1]/input')
            file_input.send_keys(prices_file_path)
            auto_web.click(CONTINUE_XPATH)  # continue button
            auto_web.click(CONTINUE_XPATH2)  # continue button
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
            CHANGE_UI_XPATH = '//*[@id="tcg-input-14"]'

            tcg_web = Tcg_web()
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
            return
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

def upload_tcgplayer_prices(file_path):
    auto_web = Tcg_web()
    # auto_web.handle_tcg_login()
    # input('Press Enter To Continue')
    # auto_web.switch_to.window(auto_web.window_handles[-1])
    upload_prices(auto_web, file_path)

