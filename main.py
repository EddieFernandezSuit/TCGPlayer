from print_envelopes.get_file_path import get_file_path
from print_envelopes.print_envelopes import print_from_csv
from print_envelopes.read_gmail import email_to_csv
from edlib import InputLoop
import datetime
import pandas as pd
import numpy as np
import os
import config

# python -m PyInstaller main.py

def replace(add_cards):
    for suffix in [' - C', ' - L', ' - R', ' - U', ' - T'] + [' - #' + str(x) for x in reversed(range(500))]:
        add_cards["Name"] = add_cards["Name"].str.replace(suffix, '')

def order_by_set():
    new_cards_file_path = get_file_path()
    set_order_file_path = "data/set_order.csv.csv"

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

def proccess_new_cards():
    email_cards_file_path = email_to_csv()
    new_cards_df = pd.read_csv(email_cards_file_path)

    def update_condition(row):
        print(row)
        condition = row['Condition']
        if row['Printing'] == 'Foil':
            condition += ' Foil'
        if row['Language'] != 'English':
            condition += ' - ' + row['Language']
        return condition
    
    new_cards_df['Condition'] = new_cards_df.apply(update_condition, axis=1)
    new_cards_df["Price Each"] = new_cards_df["Price Each"].str.strip("$").astype(float)

    lot = input('Enter Lot number: ')
    new_cards_df['Lot'] = lot
    inventory_filename = 'data/inventory.csv'
    inventory = pd.read_csv(inventory_filename)
    inventory = pd.concat([inventory, new_cards_df], ignore_index=True)
    inventory.to_csv(inventory_filename, index = False)

    new_cards_df = new_cards_df.rename(columns={"Quantity":"Add to Quantity","Name":"Product Name","Set":"Set Name","SKU":"TCGplayer Id","Price Each":"TCG Marketplace Price"})    
    new_cols = ["Title", "Number", "Rarity", "TCG Market Price","TCG Direct Low","TCG Low Price With Shipping","TCG Low Price","Total Quantity","Photo URL"]
    new_cards_df = new_cards_df.assign(**{"Product Line": "Magic"}, **{col: '' for col in new_cols})

    new_cards_df.to_csv(email_cards_file_path, index=False)

def update_inventory_and_sales(directory):
    prefixes = ["_TCGplayer_ShippingExport","TCGplayer_PullSheet","TCGplayer__MyPricing"]

    shipping_file_path, pullsheet_file_path, pricing_file_path = [get_file_matching_prefix(directory, prefix) for prefix in prefixes]

    print_from_csv(shipping_file_path)

    inventory_filename = "data/inventory.csv"
    sales_filename = "data/sales.csv"

    file_paths = [pullsheet_file_path, pricing_file_path, sales_filename, inventory_filename]
    cards_df, pricing_df, sales_df, inventory_df = [pd.read_csv(file_path) for file_path in file_paths]

    pricing_df = pricing_df.rename(columns={'TCG Marketplace Price': 'Price Each', "Set Name": "Set"})

    cards_df = cards_df[:-1]
    quantity_series = cards_df["Quantity"]
    cards_df = pd.merge(cards_df, pricing_df, on=['Product Name', 'Set', 'Condition'], how='left')
    cards_df = cards_df.drop(columns=[col for col in cards_df.columns if col not in sales_df.columns])
    new_columns = {'Lot':0,'ShipType':'normal','Date':datetime.date.today()}
    cards_df = cards_df.assign(**new_columns)

    for index, row in cards_df.iterrows():
        for _ in range(int(quantity_series[index])):
            matching_inventory = inventory_df[(inventory_df["Product Name"] == cards_df["Product Name"][index])
                    & (inventory_df["Set"] == cards_df["Set"][index])
                    & (inventory_df["Condition"] == cards_df['Condition'][index])]
            
            if not matching_inventory.empty:
                jindex = matching_inventory.index[0]
                cards_df.at[index, 'Lot'] = inventory_df.at[jindex, "Lot"]

                inventory_df.at[jindex, "Quantity"] -= 1

                if inventory_df.at[jindex, "Quantity"] == 0:
                    inventory_df = inventory_df.drop([jindex])

            sales_df = pd.concat([sales_df, cards_df.iloc[index:index+1]])
        
    inventory_df.to_csv(inventory_filename, index=False)
    sales_df.to_csv(sales_filename, index=False)

    os.remove(shipping_file_path)
    os.remove(pullsheet_file_path)
    os.remove(pricing_file_path)

def remove_cards_under_10_cents():
    cards_file_path = get_file_path()
    df = pd.read_csv(cards_file_path)
    prices = df["Price Each"].str.strip('$').astype(float)
    df.drop(df[prices < 0.1].index, inplace=True)
    df.to_csv(cards_file_path, index=False)

def find_matching_cards():
    inventory_file_path = "data/inventory.csv"
    cards_file_path = get_file_path()

    inventory_df = pd.read_csv(inventory_file_path)
    cards_df = pd.read_csv(cards_file_path)

    matching_cards_df = inventory_df.merge(cards_df, on="Name", how="inner")
    return matching_cards_df

def merge_duplicates():
    csv_filename = get_file_path()
    df = pd.read_csv(csv_filename)
    df = df.groupby(['Product Name', 'Set Name', 'Printing', 'Condition', 'Language', 'TCGplayer Id', 'TCG Marketplace Price'], as_index=False)['Add to Quantity'].sum()
    df.to_csv(csv_filename, index=False)
    
def get_revenue():
    revenue_df = pd.read_csv("data/sales.csv")
    revenue_df['Date'] = pd.to_datetime(revenue_df['Date'])
    revenue_df = revenue_df[(revenue_df['Date'] > datetime.datetime(2022, 11, 13)) & (revenue_df['Date'] < datetime.datetime.now())]
    revenue_df = revenue_df.groupby('Lot')['Price'].sum()
    revenue_df = revenue_df.round(2)
    revenue_df.to_csv('data/revenue.csv', index=False, header=True)

def adjust_card_prices(flat_discount: float = 0.01, percentage: float = 1) -> None:
    """Change the prices of the cards in the CSV file"""
    prices_file_name = get_file_path()
    df = pd.read_csv(prices_file_name)

    df['TCG Market Price'] = df['TCG Market Price'].fillna(0.01)
    df['TCG Low Price'] = df['TCG Low Price'].fillna(0.01)

    df['TCG Marketplace Price'] = np.maximum((df["TCG Market Price"] * percentage), df["TCG Low Price"], flat_discount + .01) - flat_discount

    df.to_csv(prices_file_name, index=False)

DIRECTORY = config.DOWNLOADS_DIRECTORY

commands = [
    {'text': 'Get cards from email then add to inventory then create email.csv', 'action': proccess_new_cards},
    {'text': 'Find and Print TCGPlayer Sales', 'action': lambda: update_inventory_and_sales(DIRECTORY)},
    {'text': 'Remove cards worth less than $0.10 market price from a selected file','action': remove_cards_under_10_cents},
    {'text': 'Find cards that are in a selected file and in "data/inventory.csv"','action': find_matching_cards},
    {'text': 'Combine duplicate cards in a selected file','action': merge_duplicates},
    {'text': 'Create "data/revenue.csv"','action': get_revenue},
    {'text': 'Change Prices','action': adjust_card_prices}
]

InputLoop(commands)