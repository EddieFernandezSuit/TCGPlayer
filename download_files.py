from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from new_auto_web import NewAutoWeb
import time
from config import *

class Tcg_web(NewAutoWeb):
    def handle_tcg_login(self):
        input('Press Enter after logging in to TCGPlayer To Continue')
        # TCG_URL = 'https://store.tcgplayer.com/admin/pricing'
        # self.go(TCG_URL)
        self.switch_to.window(self.window_handles[-1])

    def set_items_per_page(self, items):
        # ROWS_PER_PAGE_XPATH = '//*[@id="tcg-input-198"]'
        # number_of_orders_to_show = self.find(ROWS_PER_PAGE_XPATH)
        # Select(number_of_orders_to_show).select_by_value(str(items))
        # ROWS_PER_PAGE_XPATH = '//*[@id="single-spa-application:@tcgplayer/sellerportal-orders"]/div/div/div/div/div[4]/div/div/div[3]/div[1]/div/div/div/div/div[2]'
        ROWS_PER_PAGE_XPATH = '//*[@id="single-spa-application:@tcgplayer/sellerportal-orders"]/div/div/div/div/div[4]/div/div/div[3]/div[1]/div/div/div'
        MAX_LIST_XPATH = '//*[@id="tcg-base-dropdown-201-dropdown-item-4"]/span'
        self.click(ROWS_PER_PAGE_XPATH)
        self.click(MAX_LIST_XPATH)

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
    tcg = Tcg_web(isLocal=True)
    tcg.handle_tcg_login()
    tcg.download_pricing()
    time.sleep(2)
    return tcg

def upload_prices(auto_web: NewAutoWeb, prices_file_path):
    auto_web.go("https://store.tcgplayer.com/admin/pricing")
    time.sleep(1)
    auto_web.click('/html/body/div[4]/div/div[4]/div[2]/pricing-search/div[4]/pricing-actions/div[1]/div[1]/div/input[4]')
    file_input = auto_web.find('/html/body/div[4]/div/div[6]/pricing-dialog/div/div/div[2]/pricing-importer/div/div/div[1]/input')
    file_input.send_keys(prices_file_path)
    auto_web.click( '/html/body/div[4]/div/div[6]/pricing-dialog/div/div/div[2]/pricing-importer/div/div/div[2]/input')
    auto_web.click('/html/body/div[4]/div/div[6]/pricing-dialog/div/div/div[2]/pricing-importer/div/div/div/input[2]')  # continue button
    auto_web.click('/html/body/div[4]/div/div[6]/pricing-dialog/div/div/div[2]/pricing-importer/div/div/div/input[3]')  # move to live button
    # auto_web.click('/html/body/div[4]/div/div[6]/pricing-dialog/div/div/div[2]/pricing-move-to-live/div/div/div/input[2]')  # confirm move to live button
    # auto_web.click('/html/body/div[4]/div/div[6]/pricing-dialog/div/div/div[2]/pricing-move-to-live/div/div/div[2]/input')  # close button
    # auto_web.quit()

def download_files_normal():
    URL = "https://store.tcgplayer.com/admin/orders/orderlist"
    READY_TO_SHIP_BUTTON = '//*[@id="OrderIndex_QuickFilters_RadioReadytoShip"]'
    MARK_AS_SHIPPED_BUTTON = '//*[@id="single-spa-application:@tcgplayer/sellerportal-orders"]/div[1]/div[1]/div[1]/div[1]/div[4]/div[1]/div[1]/div[2]/div[1]/div[1]/div[1]/button[3]/span[2]'
    EXPORT_SHIPPING_BUTTON = '//*[@id="single-spa-application:@tcgplayer/sellerportal-orders"]/div[1]/div[1]/div[1]/div[1]/div[4]/div[1]/div[1]/div[2]/div[1]/div[1]/div[1]/button[2]/span[2]'
    PACKING_SLIP_XPATH = '//*[@id="single-spa-application:@tcgplayer/sellerportal-orders"]/div/div/div/div/div[4]/div/div/div[2]/div/div/div[1]/div[2]/div/button'
    PACKING_SLIP_XPATH2 = '//*[@id="tcg-popover-2604-content"]/div/div[2]/button[1]'
    

    tcg_web = Tcg_web()
    tcg_web.handle_tcg_login()
    tcg_web.download_pricing()
    tcg_web.go(URL)
    # tcg_web.set_items_per_page(100)
    time.sleep(2)
    tcg_web.click(READY_TO_SHIP_BUTTON)
    time.sleep(2)
    tcg_web.click_all_results()
    tcg_web.click_pullsheet()
    tcg_web.click(PACKING_SLIP_XPATH)
    tcg_web.click(PACKING_SLIP_XPATH2)
    # tcg_web.click(PACKING_SLIP_XPATH2)
    # tcg_web.click(PACKING_SLIP_XPATH2)
    # tcg_web.click(PACKING_SLIP_XPATH2)
    # tcg_web.wait(5)
    tcg_web.click(EXPORT_SHIPPING_BUTTON)
    tcg_web.click(identifier=MARK_AS_SHIPPED_BUTTON)
    tcg_web.quit()

def download_files_direct():
    auto_web = Tcg_web()
    auto_web.handle_tcg_login()
    auto_web.download_pricing()
    auto_web.go("https://store.tcgplayer.com/admin/ro")
    auto_web.click(identifier="/html/body/div[4]/div/div[6]/div[2]/table/tbody/tr[1]/td[1]/a")
    auto_web.click(identifier='//*[@id="btnPackingSlip"]')
    auto_web.click(identifier='//*[@id="btnPackingSlipCSV"]')
    auto_web.quit()


def upload_tcgplayer_prices(file_path):
    auto_web = NewAutoWeb()
    input('Press Enter To Continue')
    auto_web.switch_to.window(auto_web.window_handles[-1])
    upload_prices(auto_web, file_path)

