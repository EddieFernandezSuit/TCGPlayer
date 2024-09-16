import json
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

# python -m PyInstaller main.py

def order_by_set():
    new_cards_file_path = get_file_path()
    set_order_file_path = PROJECT_DIRECTORY + "data/set_order.csv.csv"
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
    # email_cards_file_path = config.PROJECT_DIRECTORY + 'data/email_cards.csv'
    new_cards_df = pd.read_csv(email_cards_file_path)

    if filter:
        new_cards_df = remove_cards_under(df=new_cards_df, price_line=.2)
        print(new_cards_df)

    def update_condition(row):
        condition = row['Condition']
        if row['Printing'] == 'Foil':
            condition += ' Foil'
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

def proccess_sales(directory, type='normal'):
    directory = DOWNLOADS_DIRECTORY

    if type == 'normal':
        download_files_normal()
        prefixes = ["_TCGplayer_ShippingExport","TCGplayer_PullSheet","TCGplayer__MyPricing"]
        paths = [get_file_matching_prefix(directory, prefix) for prefix in prefixes]
        shipping_file_path, pullsheet_file_path, pricing_file_path = paths
        print_from_csv(shipping_file_path)

    else:
        download_files_direct()
        prefixes = ["TCGplayer_PullSheet","TCGplayer__MyPricing"]
        paths = [get_file_matching_prefix(directory, prefix) for prefix in prefixes]
        pullsheet_file_path, pricing_file_path = paths
    
    inventory_file_path = PROJECT_DIRECTORY + "data/inventory.csv"
    sales_file_path = PROJECT_DIRECTORY + "data/sales.csv"
    file_paths = [pullsheet_file_path, pricing_file_path, sales_file_path, inventory_file_path]
    pullsheet_df, pricing_df, sales_df, inventory_df = [pd.read_csv(file_path) for file_path in file_paths]
    pricing_df = pricing_df.rename(columns={'TCG Marketplace Price': 'Price Each', "Set Name": "Set"})
    pullsheet_df = pullsheet_df[:-1]
    quantity_series = pullsheet_df["Quantity"]
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

    new_pullsheet_file_path = rearrange_pullsheet(pullsheet_file_path)
    sort_cards(new_pullsheet_file_path)

    for path in paths:
        os.remove(path)

def rearrange_pullsheet(file_path):
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
    # df.to_csv(cards_file_path, index=False)
    # print(df)
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
    percentage = 0.99
    flat_discount = 0.01
    minimum = 0.1

    market_price = row['TCG Market Price']
    # price = (market_price * percentage) - flat_discount
    if market_price < 1:
        price =  market_price * percentage
    elif market_price < 3:
        price = market_price * 2
    elif market_price < 20:
        price = market_price + 1.27
    elif market_price < 250:
        price = market_price + 4.17
    else:
        price = market_price + 7.5

    price = max(price, row['TCG Low Price'], row["TCG Direct Low"]) - flat_discount
    # price = price - flat_discount
    return max(price, minimum)
    
    # return max(price - flat_discount, row["TCG Low Price"] - flat_discount, row['TCG Direct Low'] - flat_discount, minimum)

def adjust_card_prices(prices_file_name = ''):
    """Change the prices of the cards in the CSV file"""
    # if prices_file_name == '':
    tcg = download_pricing()
    prices_file_name = get_file_matching_prefix(DOWNLOADS_DIRECTORY, 'TCGplayer__MyPricing')
    # print(prices_file_name)
    # return
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

    # autoweb.get(SHIPPING_LABEL_URL)
    # input('Press Enter after logging in To Continue')

    # if tcg.find_elements(By.XPATH, EMAIL_XPATH).size() > 0:
    #     tcg.find_element(By.XPATH, EMAIL_XPATH).clear()
    #     tcg.find_element(By.XPATH, EMAIL).clear()
    #     tcg.fill(type=By.XPATH, identifier=EMAIL_XPATH, input_string=EMAIL)
    #     tcg.fill(type=By.XPATH, identifier=PASSWORD_XPATH, input_string=PASSWORD)
    #     tcg.click(identifier=LOGIN_XPATH)
    #     input('Press Enter after logging in To Continue')
    # else:
    #     pass
    
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
    ]

    autoweb = NewAutoWeb(commands=commands)

commands = [
    {'text': 'Process new cards', 'action': lambda: proccess_new_cards()},
    {'text': 'Process new cards; remove under', 'action': lambda: proccess_new_cards(filter=True)},
    {'text': 'Process Sales Normal', 'action': lambda: proccess_sales(DOWNLOADS_DIRECTORY)},
    {'text': 'Process Sales Direct', 'action': lambda: proccess_sales(DOWNLOADS_DIRECTORY, 'direct')},
    {'text': 'Remove cards under','action': remove_cards_under},
    {'text': 'Find cards that are in a selected file and in "data/inventory.csv"','action': find_matching_cards},
    {'text': 'Combine duplicate cards in a selected file','action': merge_duplicates},
    {'text': 'Create "data/revenue.csv"','action': get_revenue},
    {'text': 'Change Prices','action': adjust_card_prices},
    {'text': 'Analyze value change over time', 'action': inventory_value_change_over_time},
    {'text': 'Sort cards by set', 'action': sort_cards},
    {'text': 'create shipping label', 'action': create_shipping_label}
]

InputLoop(commands, False)


def custom():
    def filter():
        cost_filter = .2
        a = df.loc[df['TCG Market Price'] > cost_filter,'TCG Market Price'].sum()
        print(a)
        a = df.loc[df['TCG Market Price'] > cost_filter,'TCG Market Price'].count()
        print(a)
        a = df['TCG Market Price'].sum()
        print(a)
    
    def change(row):
        return max(.1, row['TCG Market Price'])
    
    
    file_name = get_file_matching_prefix(PROJECT_DIRECTORY, 'TCGplayer')
    df = pd.read_csv(file_name)
    df['TCG Marketplace Price'] = df.apply(lambda row : change(row), axis=1)
    df['Add To Quantity'] = 1
    df.to_csv(file_name, index=False)

# custom()


def count_cards():
    ORDERS_PATH = 'TCGplayer_PullSheet_20240913_170005.csv'
    PRICING_PATH = 'TCGplayer__MyPricing_20240913_050048.csv'
    orders_df = pd.read_csv(ORDERS_PATH)
    pricing_df = pd.read_csv(PRICING_PATH)
    pricing_df = pricing_df.rename(columns={'Set Name': 'Set'})
    df = pd.merge(orders_df, pricing_df, on=['Product Name', 'Condition', 'Set'])
    df = df[df['TCG Marketplace Price'] <= 1]
    count = df.count()
    df.to_csv('T')
    print(df)
    print(count)

# count_cards()