import csv
from new_auto_web import NewAutoWeb
from print_envelopes import *
from download_files import *
from config import PROJECT_DIRECTORY, DOWNLOADS_DIRECTORY
from edlib import get_file_path, InputLoop
from constants import *
import datetime
import pandas as pd
import os
import packing_slip
import json
import sys

# python -m PyInstaller main.py

SALES_PATH = 'data/sales.csv'
COST_PATH = 'data/other_costs.csv'

def order_by_set():
    new_cards_file_path = get_file_path()
    set_order_file_path = PROJECT_DIRECTORY + "data/set_order.csv"
    new_cards = pd.read_csv(new_cards_file_path)
    set_order = pd.read_csv(set_order_file_path)
    new_cards = pd.merge(new_cards, set_order, on='Set', how='left')
    new_cards = new_cards.sort_values('Order')
    new_cards = new_cards.drop('Order', axis=1)
    new_cards.to_csv(new_cards_file_path, index=False)

def get_file_matching_prefix(dir_path: str, file_name_prefix: str) -> str:
    matching_files = [file for file in os.listdir(dir_path) if file.startswith(file_name_prefix)]
    last_filename = os.path.join(dir_path, max(matching_files)) if matching_files else None 
    return last_filename

def proccess_new_cards(filter=False):
    # email_cards_file_path = 'C:\\Users\\ferna\\Downloads\\TCGPlayer\\data\\email_cards.csv'
    email_cards_file_path = email_to_csv()
    new_cards_df = pd.read_csv(email_cards_file_path)

    if filter:
        new_cards_df = remove_cards_under(df=new_cards_df, price_line=.2)

    # def update_condition(row):
    #     condition = row['Condition']
    #     if 'printing' in row and row['Printing'] != 'Normal':
    #         condition += ' ' +  row['Printing']
    #     if 'printing' in row and row['Language'] != 'English':
    #         condition = f"{condition} - {row['Language']}"
    #     return condition

    # new_cards_df['Condition'] = new_cards_df.apply(update_condition, axis=1)
    # if 'Price Each' in new_cards_df:
        # new_cards_df["Price Each"] = new_cards_df["Price Each"].str.strip("$").astype(float)
        # new_cards_df = new_cards_df.rename(columns={'Price Each': 'TCG Market Price'})

    new_cards_df['TCG Direct Low'] = .01
    new_cards_df['TCG Low Price'] = .01
    # new_cards_df['Price Each'] = new_cards_df.apply(lambda row: calculate_price(row), axis=1)
    # if 'Printing' in new_cards_df:
        # new_cards_df = new_cards_df.drop('Printing', axis=1)
    # if 'Language' in new_cards_df:
        # new_cards_df = new_cards_df.drop('Language', axis=1)
    # lot = input('Enter Lot number: ')
    new_cards_df['Lot'] = AUTO_LOT
    inventory_filename = PROJECT_DIRECTORY + 'data/inventory.csv'
    inventory = pd.read_csv(inventory_filename)
    inventory = pd.concat([inventory, new_cards_df], ignore_index=True)
    inventory.to_csv(inventory_filename, index = False)

    # new_cards_df = new_cards_df.rename(columns={"Quantity":"Add to Quantity","Name":"Product Name","Set":"Set Name","SKU":"TCGplayer Id","Price Each":"TCG Marketplace Price"})    
    # new_cols = ["Title", "Number", "Rarity", "TCG Market Price","TCG Direct Low","TCG Low Price With Shipping","TCG Low Price","Total Quantity","Photo URL"]
    # new_cards_df = new_cards_df.assign(**{"Product Line": "Magic"}, **{col: '' for col in new_cols})
    new_cards_df['Product Line'] = 'Magic'
    new_cards_df['TCG Marketplace Price'] = new_cards_df['TCG Market Price']
    new_cards_df['TCG Marketplace Price'] = new_cards_df.apply(lambda row: calculate_price(row), axis=1)
    
    new_cards_df.to_csv(email_cards_file_path, index=False)
    # merge_duplicates(email_cards_file_path)
    tcg = Tcg_web()
    tcg.upload_prices(email_cards_file_path)

def handle_file_exist(file_name):
    while not os.path.isfile(file_name):
        input('File ' + file_name + ' does not exist')

def proccess_new_cards_magic_sorter():
    download_results_gmail()
    new_cards_file_path = DOWNLOADS_DIRECTORY + 'results.csv'
    handle_file_exist(new_cards_file_path)
    new_cards_df = pd.read_csv(new_cards_file_path)
    print(new_cards_df[['Add to Quantity', 'Set Name', 'Product Name', 'Condition']])
    input('Press Enter to continue if listed cards are correct')
    new_cards_df['Price Each'] = new_cards_df.apply(lambda row: calculate_price(row), axis=1)
    new_cards_df['Lot'] = AUTO_LOT

    inventory_filename = PROJECT_DIRECTORY + 'data/inventory.csv'
    inventory = pd.read_csv(inventory_filename)
    inventory = pd.concat([inventory, new_cards_df], ignore_index=True)
    inventory.to_csv(inventory_filename, index = False)
    new_cards_df.to_csv(new_cards_file_path, index=False)
    tcg = Tcg_web()
    tcg.upload_prices(new_cards_file_path)

    pricing = get_file_matching_prefix(DOWNLOADS_DIRECTORY, 'TCGplayer__MyPricing')
    create_sorter_inventory_csv(pricing)
    
    os.remove(pricing)
    # os.remove(new_cards_file_path)

def process_sales(type='normal'):
    ANALYSIS_FILE_PATH = PROJECT_DIRECTORY + "data/analysis_data.csv"
    if type == 'normal':
        number_of_orders = download_files_normal()
        # number_of_orders = 46
        df = pd.read_csv(ANALYSIS_FILE_PATH)
        LAST_DATE = pd.to_datetime(df.iloc[-1]['date'])
        TODAY = datetime.datetime.now()

        date_diff = (TODAY - LAST_DATE).days
        if date_diff == 0:
            date_diff = 3

        new_row = {
            "date": TODAY,
            "orders": number_of_orders,
            "min": 0.02,
            "%": .97,
            "minus": 0.02,
            "day": TODAY.strftime("%A"),
            "days": date_diff,
            "orders/day": round(number_of_orders / date_diff, 2),
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(ANALYSIS_FILE_PATH, index=False)

        time.sleep(1)
        shipping_prefix = "_TCGplayer_ShippingExport"
        pullsheet_prefix = "TCGplayer_PullSheet"
        
        shipping_path = get_file_matching_prefix(DOWNLOADS_DIRECTORY, shipping_prefix)
        pullsheet_path = get_file_matching_prefix(DOWNLOADS_DIRECTORY, pullsheet_prefix)
        print_from_csv(shipping_path)
    else:
        download_files_direct()
        time.sleep(1)
        pullsheet_prefix = 'R2024'
        pullsheet_path = get_file_matching_prefix(DOWNLOADS_DIRECTORY, pullsheet_prefix)
        with open(pullsheet_path, 'r+') as fp:
            lines = fp.readlines()
            fp.seek(0)
            fp.truncate()
            fp.writelines(lines[1:])

    pricing_prefix = "TCGplayer__MyPricing"
    pricing_path = get_file_matching_prefix(DOWNLOADS_DIRECTORY, pricing_prefix)
    sales_file_path = PROJECT_DIRECTORY + "data/sales.csv"
    inventory_file_path = PROJECT_DIRECTORY + "data/inventory.csv"
    paths = [pullsheet_path, pricing_path, sales_file_path, inventory_file_path]
    pullsheet_df, pricing_df, sales_df, inventory_df = [pd.read_csv(file_path) for file_path in paths]
    pricing_df = pricing_df.rename(columns={'TCG Marketplace Price': 'Price Each', "Set Name": "Set"})
    pullsheet_df = pullsheet_df[:-1]
    quantity_series = pullsheet_df["Quantity"]

    if type =='direct':
        pullsheet_df = pullsheet_df.rename(columns={'Card Name': 'Product Name', 'Set Name': 'Set'})
    pullsheet_df = pd.merge(pullsheet_df, pricing_df, on=['Product Name', 'Set', 'Condition'], how='left')
    pullsheet_df = pullsheet_df.drop(columns=[col for col in pullsheet_df.columns if col not in sales_df.columns])
    
    new_columns = {'Lot':0,'ShipType':type,'Date':datetime.date.today()}
    pullsheet_df = pullsheet_df.assign(**new_columns)

    for index, row in pullsheet_df.iterrows():
        for _ in range(int(quantity_series[index])):
            matching_inventory = inventory_df[(inventory_df["Name"] == pullsheet_df["Product Name"][index])
                    & (inventory_df["Set"] == pullsheet_df["Set"][index])
                    & (inventory_df["Condition"] == pullsheet_df['Condition'][index])]
            
            if not matching_inventory.empty:
                jindex = matching_inventory.index[0]
                pullsheet_df.at[index, 'Lot'] = int(float(inventory_df.at[jindex, "Lot"]))
                inventory_df.at[jindex, "Quantity"] -= 1
                if inventory_df.at[jindex, "Quantity"] == 0:
                    inventory_df = inventory_df.drop([jindex])

            sales_df = pd.concat([sales_df, pullsheet_df.iloc[index:index+1]])
        
    inventory_df.to_csv(inventory_file_path, index=False)
    sales_df.to_csv(sales_file_path, index=False)

    # new_pullsheet_file_path = fix_collumns(pullsheet_df)
    # sort_cards(new_pullsheet_file_path)

    for path in [pullsheet_path, pricing_path]:
        os.remove(path)
    
    if type == 'normal':
        packing_slip_path = get_file_matching_prefix(DOWNLOADS_DIRECTORY, 'TCGplayer_PackingSlips')
        orders = packing_slip.get_orders_from_pdf(packing_slip_path)
        for order in orders:
            order.print_order()
            input('')

        if packing_slip_path:
            # webbrowser.open(packing_slip_path)
            # time.sleep(5)
            os.remove(packing_slip_path)
            os.remove(shipping_path)
            
        else:
            print('No Packing Slip')
    schedule_pickup()

def fix_collumns(file_path=None, pullsheet_df = None):
    if file_path:
        pullsheet_df = pd.read_csv(file_path)
    
    first_cols = ['Set', 'Quantity', 'Product Name', 'Condition']
    pullsheet_df = pullsheet_df[first_cols + [col for col in pullsheet_df if col not in first_cols]]
    new_pullsheet_file_path = PROJECT_DIRECTORY + 'data/pullsheet.csv'
    pullsheet_df.to_csv(new_pullsheet_file_path, index=False)
    return new_pullsheet_file_path

def remove_cards_under(cards_file_path = '', df = pd.DataFrame(), price_line=.2):
    if df.empty:
        if cards_file_path == '':
            cards_file_path = get_file_path()
        df = pd.read_csv(cards_file_path)
    
    prices = df["Price Each"].str.strip('$').astype(float)
    df.drop(df[prices < price_line].index, inplace=True)
    return df

def find_matching_cards():
    inventory_file_path = PROJECT_DIRECTORY + "data/inventory.csv"
    cards_file_path = get_file_path()

    inventory_df = pd.read_csv(inventory_file_path)
    cards_df = pd.read_csv(cards_file_path)

    matching_cards_df = inventory_df.merge(cards_df, on="Name", how="inner")
    return matching_cards_df

def merge_duplicates(file_path = None):
    if file_path:
        csv_filename = file_path
    else: 
        csv_filename = get_file_path()
    df = pd.read_csv(csv_filename)
    df = df.groupby(['Product Name', 'Set Name', 'Condition', 'TCGplayer Id', 'TCG Marketplace Price'], as_index=False)['Add to Quantity'].sum()
    df.to_csv(csv_filename, index=False)
    
def get_revenue():
    revenue_df = pd.read_csv(PROJECT_DIRECTORY + "data/sales.csv")
    revenue_df['Date'] = pd.to_datetime(revenue_df['Date'])
    revenue_df = revenue_df[(revenue_df['Date'] > datetime.datetime(2022, 11, 13)) & (revenue_df['Date'] < datetime.datetime.now())]
    revenue_df = revenue_df.groupby('Lot')['Price Each'].sum()
    revenue_df = revenue_df.round(2)
    print(revenue_df)
    revenue_df.to_csv(PROJECT_DIRECTORY + 'data/revenue.csv', header=True)

def calculate_price(row):
    PERCENT = .98
    FLAT_DISCOUNT = 0.00
    MIN = 0.03

    market_price = float(row['TCG Market Price'])
    price = round(market_price * PERCENT - FLAT_DISCOUNT, 2)

    # if market_price < 1:
    #     price =  market_price * percentage
    # elif market_price < 3:
    #     price = market_price * 2
    # elif market_price < 20:
    #     price = market_price + 1.27
    # elif market_price < 250:
    #     price = market_price + 4.17
    # else:
    #     price = market_price + 7.5

    price = max(price, row['TCG Low Price'] - .01, MIN)
    return price

def adjust_card_prices(prices_file_name = ''):
    """Change the prices of the cards in the CSV file"""
    tcg = Tcg_web()
    tcg.download_pricing()
    prices_file_name = get_file_matching_prefix(DOWNLOADS_DIRECTORY, 'TCGplayer__MyPricing')
    handle_file_exist(prices_file_name)
    df = pd.read_csv(prices_file_name)
    df['TCG Market Price'] = df['TCG Market Price'].fillna(0.01)
    df['TCG Low Price'] = df['TCG Low Price'].fillna(0.01)
    df['TCG Direct Low'] = df['TCG Direct Low'].fillna(0.01)
    df['TCG Marketplace Price'] = df.apply(lambda row: calculate_price(row), axis=1)
    df.to_csv(prices_file_name, index=False)
    tcg.upload_prices(prices_file_name)

def inventory_value_change_over_time():
    inventory_file_paths = [get_file_path(), get_file_path()]
    inventory_dfs = [pd.read_csv(inventory_file_path) for inventory_file_path in inventory_file_paths]
    individual_values_dfs = [inventory_dfs[0]['Total Quantity'] * inventory_df['TCG Market Price'] for inventory_df in inventory_dfs]
    total_values = [individual_values_df.aggregate(['sum'])['sum'] for individual_values_df in individual_values_dfs]
    print(total_values)

def sort_cards(file_path = ''):
    if file_path == '':
        file_path = get_file_path()

    df = pd.read_csv(file_path)
    df = df.drop(df.tail(1).index)
    sets = df['Set'].drop_duplicates()
    df.Set = df.Set.astype("category")
    df.Set = df.Set.cat.set_categories(sets)
    df = df.sort_values(['Set', 'Product Name'])
    df.to_csv(file_path, index=False)

def create_shipping_label():
    EMAIL_XPATH = '//*[@id="email"]'
    PASSWORD_XPATH = '//*[@id="password"]'
    EMAIL = 'fernandezeddie54@gmail.com'
    LOGIN_XPATH = '//*[@id="btnLogin"]'
    
    SHIPPING_LABEL_URL = 'https://www.paypal.com/shiplabel/create'
    CREATE_NEW_LABEL_XPATH = '//*[@id="__next"]/div/div[2]/div/div/div[2]/div/a'
    ADD_ADDRESS_XPATH = '/html/body/div[1]/div/div[2]/div[2]/div/div/div[1]/div[1]/div[3]/div/div[2]/div/div[1]/button'
    PASTE_ADDRESS_XPATH = '//*[@id="modal-container"]/div[2]/div/form/div/div[1]/button'
    ADDRESS_XPATH = '//*[@id="parseAddress"]'
    COUNTRY_XPATH = '//*[@id="countryCode"]'
    COMFIRM = '//*[@id="modal-container"]/div[2]/div/form/div/button'
    CITY='//*[@id="cityLocality"]'
    STATE='//*[@id="stateProvince"]'
    ZIP='//*[@id="postalCode"]'
    COMFIM_CONTINUE='//*[@id="confirm-address-modal-container"]/div[3]/div[1]/button/span'

    TCG_MAILING_ADDRESS = "TCGplayer: RI\n5640 E Taft Road #3267\nSyracuse, NY 13220"

    PACKAGE_TYPE_XPATH = '//*[@id="headlessui-listbox-button-13"]'

    commands = [
        ['get', SHIPPING_LABEL_URL],
        ['wait'],
        ['click', CREATE_NEW_LABEL_XPATH],
        ['click', ADD_ADDRESS_XPATH],
        ['click', PASTE_ADDRESS_XPATH],
        ['fill', ADDRESS_XPATH, TCG_MAILING_ADDRESS],
        ['select', COUNTRY_XPATH, 'US'],
        ['fill', CITY, 'Syracuse'],
        ['fill', STATE, 'NY'],
        ['fill', ZIP, '13220'],
        ['click', COMFIRM],
        ['click', COMFIM_CONTINUE],
        ['click', PACKAGE_TYPE_XPATH],
    ]

    autoweb = NewAutoWeb(commands=commands)

def price_set():
    def filter(df):
        cost_filter = .2
        filter_df = df[~df['Product Name'].str.contains('Borderless')]
        filter_df = filter_df[~filter_df['Product Name'].str.contains('Showcase')]
        filter_df = filter_df[~filter_df['Product Name'].str.contains('Extended Art')]
        print(filter_df)

        price_filter_df = filter_df.loc[filter_df['TCG Market Price'] > cost_filter,'TCG Market Price',]
        filter_sum = price_filter_df.sum()
        filter_count = price_filter_df.count()
        
        sum = filter_df['TCG Market Price'].sum()
        count = filter_df['TCG Market Price'].count()
        print('filter sum: ',filter_sum,', filter count: ',filter_count,', sum: ',sum,', count:',count)
    
    def change(row):
        return max(.1, row['TCG Market Price'])
    
    file_name = get_file_matching_prefix(DOWNLOADS_DIRECTORY, 'TCGplayer')
    df = pd.read_csv(file_name)
    filter(df)

def count_cards():
    orders_path = None
    pricing_path = None
    while orders_path == None or pricing_path == None:
        orders_path = get_file_matching_prefix(DOWNLOADS_DIRECTORY, 'TCGplayer_PullSheet')
        pricing_path = get_file_matching_prefix(DOWNLOADS_DIRECTORY, 'TCGplayer__MyPricing')
        if not orders_path or not pricing_path:
            input('File not found. Print Enter to continue')
    
    orders_df = pd.read_csv(orders_path)
    pricing_df = pd.read_csv(pricing_path)
    # filtered_df = pricing_df[pricing_df['TCG Market Price'] < .1]
    # print(filtered_df['Total Quantity'].sum())
    # filtered_df.to_csv('S')
    pricing_df = pricing_df.rename(columns={'Set Name': 'Set'})
    df = pd.merge(orders_df, pricing_df, on=['Product Name', 'Condition', 'Set'])
    df = df[df['TCG Market Price'] < .1]
    count = df['Quantity'].sum()
    print(df)
    print(count)
    df.to_csv('T')

def enter_csv(amount, name, lot):
    amount = float(amount)
    date = datetime.date.today()

    if amount < 0:
        path = COST_PATH
        new_row = {'Description': [name],'Value': [amount],'Date': [date]}

    else:
        new_row = {'Set': [''],'Condition': [''],'Product Name': [name],'Price Each':[amount],'Lot':[lot],'Date':[date],'ShipType':['']}
        path = SALES_PATH

    df = pd.read_csv(path)
    new_row_df = pd.DataFrame(new_row)
    df = pd.concat([df, new_row_df])
    print(df)
    df.to_csv(path, index=False)

def enter_BECU(amount, transfer_type):
    amount = float(amount)
    # 1 is C to T 2 is T to C
    BECU_TRANSFER_URL = 'https://onlinebanking.becu.org/BECUBankingWeb/Transfers/AddTransfer.aspx'
    USERNAME_XPATH = '//*[@id="ctlSignon_txtUserID"]'
    PASSWORD_XPATH = '//*[@id="ctlSignon_txtPassword"]'
    LOGIN_XPATH = '//*[@id="ctlSignon_btnLogin"]'
    FROM_XPATH = '//*[@id="ctlWorkflow_ddlAddFromAccount"]'
    TO_XPATH = '//*[@id="ctlWorkflow_ddlAddToAccount"]'
    CHECKING_VALUE = '1'
    TCG_VALUE = '3'
    AMOUNT_XPATH = '//*[@id="ctlWorkflow_txtAddTransferAmount"]'
    CONTINUE_XPATH = '//*[@id="ctlWorkflow_btnAddNext"]'
    COMFIRM_XPATH = '//*[@id="ctlWorkflow_btnAddVerifyAddTransfer"]'

    from_value = CHECKING_VALUE if transfer_type == 1 else TCG_VALUE
    to_value = TCG_VALUE if transfer_type == 1 else CHECKING_VALUE
    amount = abs(amount)

    commands = [
        ['go', BECU_TRANSFER_URL],
        # ['fill', USERNAME_XPATH, BECU_USERNAME],
        # ['fill', PASSWORD_XPATH, BECU_PASSWORD],
        ['click', LOGIN_XPATH],
        ['select', FROM_XPATH, from_value ],
        ['select', TO_XPATH, to_value],
        ['fill', AMOUNT_XPATH, amount],
        ['click', CONTINUE_XPATH],
        ['click', COMFIRM_XPATH]
    ]

    NewAutoWeb(commands=commands)

def manual_sale_cost():
    amount = float(input('Enter amount: '))
    transfer_type = 2 if amount < 0 else 1
    name = input('Enter name: ')
    lot = 0
    if transfer_type == 1:
        lot = input('Lot: ')
    enter_BECU(amount, transfer_type)
    enter_csv(amount, name, lot)

def process_sales_combined():
    process_sales()
    process_sales('direct')

def delete_files_not_ending_in_zero(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        if os.path.isfile(file_path) and not filename.endswith('_0.jpg'):
            try:
                os.remove(file_path)
                print(f"Deleted: {filename}")
            except Exception as e:
                print(f"Error deleting {filename}: {e}")

def schedule_pickup(naw=None):
    URL = 'https://tools.usps.com/schedule-pickup-steps.htm'
    FIRST_NAME_XPATH = '//*[@id="firstName"]'
    LAST_NAME_XPATH = '//*[@id="lastName"]'
    STREET_ADDRESS_XPATH = '//*[@id="addressLineOne"]'
    CITY_XPATH = '//*[@id="city"]'
    STATE_XP = '//*[@id="state"]'
    ZIP_CODE_XP = '//*[@id="zipCode"]'
    PHONE_XP = '//*[@id="phoneNumber"]'
    EMAIL_XP = '//*[@id="emailAddress"]'
    CHECK_AV_XP = '//*[@id="webToolsAddressCheck"]'
    IS_DOG_XP = '//*[@id="first-radio-verification"]'
    LOCATION_PACKAGE_XP = '//*[@id="packageLocation"]'
    TIME_XP = '//*[@id="pickup-regular-time"]'
    NEXT_DAY_CLASS = 'ui-datepicker-current-day'
    USPS_GROUND_ADVANTAGE_XP = '//*[@id="countGroundAdvantage"]'
    TOTAL_WEIGHT_XP = '//*[@id="totalPackageWeight"]'
    DOES_NOT_CONTAIN_HAZARDOUS_XP = '//*[@id="hazmat-no"]'
    I_HAVE_READ_THE_TERMS_XP = '/html/body/div[9]/div/div[3]/div/div[6]/label'
    SCHEDULE_PICKUP_XP = '//*[@id="schedulePickupButton"]'

    PHONE = '253-507-3193'
    EMAIL = 'fernandezeddie54@gmail.com'
    LOCATION_PACKAGE = 'Knock'

    number_of_packages = input('How many USPS Ground Advantage packages? This will also be the total weight in lbs: ')
    
    commands = [
        ['go', URL],
        ['fill', FIRST_NAME_XPATH, FIRST_NAME],
        ['fill', LAST_NAME_XPATH, LAST_NAME],
        ['fill', STREET_ADDRESS_XPATH, STREET_ADDRESS],
        ['fill', CITY_XPATH, CITY],
        ['select', STATE_XP, STATE],
        ['fill', ZIP_CODE_XP, ZIP_CODE],
        ['fill', PHONE_XP, PHONE],
        ['fill', EMAIL_XP, EMAIL],
        ['click', CHECK_AV_XP],
        ['click', IS_DOG_XP],
        ['select', LOCATION_PACKAGE_XP, LOCATION_PACKAGE],
        ['click', TIME_XP],
        ['click', NEXT_DAY_CLASS, By.CLASS_NAME],
        ['fill', USPS_GROUND_ADVANTAGE_XP, number_of_packages],
        ['fill', TOTAL_WEIGHT_XP, number_of_packages],
        ['click', DOES_NOT_CONTAIN_HAZARDOUS_XP],
        ['click', I_HAVE_READ_THE_TERMS_XP],
        ['click', SCHEDULE_PICKUP_XP],
    ]

    if naw is None:
        NewAutoWeb(commands)
    else:
        naw.execute_commands(commands)

def create_sorter_inventory_csv(filepath=''):
    input_file = filepath
    output_file = r'\\magic-sorter-2aaf4\\Public\\interesting.csv'
    # output_file = DOWNLOADS_DIRECTORY + '\\cards to go machine'

    with open(input_file, mode='r', encoding='utf-8-sig') as infile, \
        open(output_file, mode='w', newline='', encoding='utf-8') as outfile:

        reader = csv.DictReader(infile)
        writer = csv.writer(outfile)
        writer.writerow(['set', 'title', 'num'])

        for row in reader:
            set_code = '*'
            title = row.get('Product Name', '').strip()
            number = '*'
            total_quantity = int(row.get('Total Quantity', ''))

            if title and total_quantity > 0:
                writer.writerow([set_code, title, number])

    print(f"Converted file saved as: {output_file}")
    return output_file

def prepare_magic_sorter():
    tcg = Tcg_web()
    tcg.download_pricing()
    inventory_filename = get_file_matching_prefix(DOWNLOADS_DIRECTORY, 'TCGplayer__MyPricing')
    create_sorter_inventory_csv(inventory_filename)
    os.remove(inventory_filename)

with open(PROJECT_DIRECTORY + '/data/settings.json', 'r') as f:
    data = json.load(f)

AUTO_LOT = data['lot']
print('Current Lot: ', AUTO_LOT)

commands = [
    {'text': 'Process new cards', 'action': lambda: proccess_new_cards()},
    {'text': 'Process new cards magic sorter', 'action': lambda: proccess_new_cards_magic_sorter()},
    {'text': 'Process new cards; remove under', 'action': lambda: proccess_new_cards(filter=True)},
    {'text': 'Process Sales Normal', 'action': lambda: process_sales()},
    {'text': 'Process Sales Direct', 'action': lambda: process_sales( 'direct')},
    {'text': 'Process Sales Combined', 'action': lambda: process_sales_combined()},
    {'text': 'Combine duplicate cards in a selected file','action': merge_duplicates},
    {'text': 'Create "data/revenue.csv"','action': get_revenue},
    {'text': 'Change Prices','action': adjust_card_prices},
    {'text': 'Analyze value change over time', 'action': inventory_value_change_over_time},
    {'text': 'Sort cards by set', 'action': sort_cards},
    {'text': 'create shipping label', 'action': create_shipping_label},
    {'text': 'price set', 'action': price_set},
    {'text': 'count cards', 'action': count_cards},
    {'text': 'manual entry', 'action': manual_sale_cost},
    {'text': 'schedule pickup', 'action': schedule_pickup},
    {'text': 'prepare magic sorter', 'action': prepare_magic_sorter},
]

if len(sys.argv) > 1:
    command = int(sys.argv[1])
else:
    command = None

InputLoop(commands, False, command)

input('Press Enter to exit')
