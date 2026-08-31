from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import time

def get_driver():
    options = Options()
    # NOT headless so you can see what's happening
    return webdriver.Chrome(options=options)

def test_pickup():
    driver = get_driver()
    try:
        URL = 'https://tools.usps.com/schedule-pickup-steps.htm'
        driver.get(URL)
        time.sleep(5)

        def fill_and_tab(field_id, value):
            el = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, field_id)))
            el.click()
            el.send_keys(value)
            el.send_keys(Keys.TAB)
            time.sleep(0.5)

        def select_and_tab(field_id, value):
            el = driver.find_element(By.ID, field_id)
            Select(el).select_by_value(value)
            el.send_keys(Keys.TAB)
            time.sleep(0.5)

        fill_and_tab('firstName', 'Eddie')
        fill_and_tab('lastName', 'Fernandez')
        fill_and_tab('addressLineOne', '5009 S State St')
        fill_and_tab('city', 'Tacoma')
        select_and_tab('state', 'WA')
        fill_and_tab('zipCode', '98409')
        fill_and_tab('phoneNumber', '253-507-3193')
        fill_and_tab('emailAddress', 'fernandezeddie54@gmail.com')
        time.sleep(2)

        btn = driver.find_element(By.ID, 'webToolsAddressCheck')
        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
        time.sleep(1)
        btn.click()
        print('Clicked check address')
        time.sleep(8)

        body_text = driver.find_element(By.TAG_NAME, 'body').text
        print('Step 2 visible:', 'Step 2' in body_text)
        print('Page snippet:', body_text[:300])

        input('Press Enter to close...')
    finally:
        driver.quit()

test_pickup()