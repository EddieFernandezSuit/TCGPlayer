from new_auto_web import NewAutoWeb
from print_envelopes import print_from_csv
from print_envelopes import email_to_csv
from download_files import *
from config import *
from edlib import get_file_path, InputLoop
import datetime
import pandas as pd
import os
from mtgsdk import Card
import webbrowser

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

def get_file_matching_prefix(dir_path, file_name_prefix):
    matching_files = [file for file in os.listdir(dir_path) if file.startswith(file_name_prefix)]
    last_file = os.path.join(dir_path, max(matching_files)) if matching_files else None 
    return last_file

def proccess_new_cards(filter=False):
    email_cards_file_path = email_to_csv()
    new_cards_df = pd.read_csv(email_cards_file_path)

    if filter:
        new_cards_df = remove_cards_under(df=new_cards_df, price_line=.2)

    def update_condition(row):
        condition = row['Condition']
        if row['Printing'] != 'Normal':
            condition += ' ' +  row['Printing']
        if row['Language'] != 'English':
            condition = f"{condition} - {row['Language']}"
        return condition

    new_cards_df['Condition'] = new_cards_df.apply(update_condition, axis=1)
    new_cards_df["Price Each"] = new_cards_df["Price Each"].str.strip("$").astype(float)
    new_cards_df = new_cards_df.rename(columns={'Price Each': 'TCG Market Price'})
    new_cards_df['TCG Direct Low'] = .01
    new_cards_df['TCG Low Price'] = .01
    new_cards_df['Price Each'] = new_cards_df.apply(lambda row: calculate_price(row), axis=1)
    new_cards_df = new_cards_df.drop('Printing', axis=1)
    new_cards_df = new_cards_df.drop('Language', axis=1)
    lot = input('Enter Lot number: ')
    new_cards_df['Lot'] = lot
    inventory_filename = PROJECT_DIRECTORY + 'data/inventory.csv'
    inventory = pd.read_csv(inventory_filename)
    inventory = pd.concat([inventory, new_cards_df], ignore_index=True)
    inventory.to_csv(inventory_filename, index = False)

    new_cards_df = new_cards_df.rename(columns={"Quantity":"Add to Quantity","Name":"Product Name","Set":"Set Name","SKU":"TCGplayer Id","Price Each":"TCG Marketplace Price"})    
    new_cols = ["Title", "Number", "Rarity", "TCG Market Price","TCG Direct Low","TCG Low Price With Shipping","TCG Low Price","Total Quantity","Photo URL"]
    new_cards_df = new_cards_df.assign(**{"Product Line": "Magic"}, **{col: '' for col in new_cols})

    new_cards_df.to_csv(email_cards_file_path, index=False)
    merge_duplicates(email_cards_file_path)
    upload_tcgplayer_prices(email_cards_file_path)

def process_sales(type='normal'):
    if type == 'normal':
        download_files_normal()
        shipping_prefix = "_TCGplayer_ShippingExport"
        shipping_path = get_file_matching_prefix(DOWNLOADS_DIRECTORY, shipping_prefix)
        time.sleep(1)
        print_from_csv(shipping_path)
        # return
        pullsheet_prefix = "TCGplayer_PullSheet"
        pullsheet_path = get_file_matching_prefix(DOWNLOADS_DIRECTORY, pullsheet_prefix)
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
                pullsheet_df.at[index, 'Lot'] = inventory_df.at[jindex, "Lot"]

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
        if packing_slip_path:
            webbrowser.open(packing_slip_path)
            time.sleep(5)
            os.remove(packing_slip_path)
        else:
            print('No Packing Slip')

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
    percentage = 1
    flat_discount = 0.01
    minimum = 0.1

    market_price = float(row['TCG Market Price'])
    price = market_price * percentage
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

    price = max(price, row['TCG Low Price'], row["TCG Direct Low"]) - flat_discount
    return max(price, minimum)

def adjust_card_prices(prices_file_name = ''):
    """Change the prices of the cards in the CSV file"""
    tcg = download_pricing()
    prices_file_name = get_file_matching_prefix(DOWNLOADS_DIRECTORY, 'TCGplayer__MyPricing')
    df = pd.read_csv(prices_file_name)
    df['TCG Market Price'] = df['TCG Market Price'].fillna(0.01)
    df['TCG Low Price'] = df['TCG Low Price'].fillna(0.01)
    df['TCG Direct Low'] = df['TCG Direct Low'].fillna(0.01)
    df['TCG Marketplace Price'] = df.apply(lambda row: calculate_price(row), axis=1)
    df.to_csv(prices_file_name, index=False)
    upload_prices(tcg, prices_file_name)

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
        cost_filter = 1
        filter_sum = df.loc[df['TCG Market Price'] > cost_filter,'TCG Market Price'].sum()
        filter_count = df.loc[df['TCG Market Price'] > cost_filter,'TCG Market Price'].count()
        sum = df['TCG Market Price'].sum()
        count = df['TCG Market Price'].count()
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

def schedule_pickup():
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

    FIRST_NAME = 'Eddie'
    LAST_NAME = 'Fernandez'
    STREET_ADDRESS = '19803 15th Ave E'
    CITY = 'Spanaway'
    STATE = 'WA'
    ZIP_CODE = '98387'
    PHONE = '253-507-3193'
    EMAIL = 'fernandezeddie54@gmail.com'
    LOCATION_PACKAGE = 'Knock'

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
        
    ]

    NewAutoWeb(commands)

commands = [
    {'text': 'Process new cards', 'action': lambda: proccess_new_cards()},
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
    {'text': 'schedule pickup', 'action': schedule_pickup}
]


# path = get_file_matching_prefix(DOWNLOADS_DIRECTORY, 'TCG')

# df = pd.read_csv(path)
# for index, row in df.iterrows():
#     print('1', row['Product Name'], '[ISD]')
InputLoop(commands, False)


# path = get_file_matching_prefix(DOWNLOADS_DIRECTORY, 'TCG')
# df = pd.read_csv(path)
# df['TCG Marketplace Price'] = df.apply(lambda row: calculate_price(row), axis=1)
# df['Add to Quantity'] = 4
# df = df[df['TCG Marketplace Price'] < .4]
# df.to_csv(DOWNLOADS_DIRECTORY + '\\new.csv', index=False)