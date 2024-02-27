from PrintEnvelopes.getFilePath import getFilePath
from PrintEnvelopes.printEnvelopes import printFromCsv
from PrintEnvelopes.readGmail import EmailToCSV
from edlib import InputLoop
import datetime
import pandas as pd
import math
import os
import re
import csv
import config

# python -m PyInstaller main.py

def moeny_to_float(s):
    return float(s.strip('$'))

def fix_data():
    sales_filename = "sales.csv"
    sales = pd.read_csv(sales_filename)
    sales['Price Each'] = sales['Price Each'].fillna(0)
    sales.to_csv(sales_filename, index=False, header=True)

def replace(addCards):
    for suffix in [' - C', ' - L', ' - R', ' - U', ' - T'] + [' - #' + str(x) for x in reversed(range(500))]:
        addCards["Name"] = addCards["Name"].str.replace(suffix, '')

def orderSets():
    filePath = getFilePath()
    newCards = pd.read_csv(filePath)
    setOrder = pd.read_csv("setOrder.csv")

    newCards = pd.merge(newCards, setOrder, on='Set', how='left')
    newCards = newCards.sort_values('Order')
    newCards = newCards.drop('Order', axis=1)

    newCards.to_csv(filePath, index=False)

def removeParentheses(str):
    return re.sub(r"\([^()]*\)", "", str)


def get_clean_data(data):
    return 0.01 if math.isnan(data) or data == '' else float(data)

def SortCSVByReleaseDate(filePath):
    newCardsdf = pd.read_csv(filePath)
    newCardsdf['Set Release Date'] = pd.to_datetime(newCardsdf['Set Release Date'])
    newCardsdf = newCardsdf.sort_values(by=['Set Release Date'], ascending=False)
    newCardsdf.to_csv(filePath, index = False)

def get_newest_file_matching_prefix(dir_path, file_name_prefix):
    lastFile = None
    for file in os.listdir(dir_path):
        if file.startswith(file_name_prefix):
            lastFile = os.path.join(dir_path, file)
    return lastFile

def addLot(new_cards_df):
    lot = input('Enter Lot number: ')
    new_cards_df['Lot'] = lot
    inventory_filename = 'inventory.csv'
    inventory = pd.read_csv(inventory_filename)
    inventory = pd.concat([inventory, new_cards_df], ignore_index=True)
    inventory.to_csv(inventory_filename, index = False)

def update_headers(new_cards_df):
    new_cards_df = new_cards_df.rename(columns={"Quantity":"Add to Quantity","Name":"Product Name","Set":"Set Name","SKU":"TCGplayer Id","Price Each":"TCG Marketplace Price"})
    new_cols = ["Product Line", "Title", "Number", "Rarity", "TCG Market Price","TCG Direct Low","TCG Low Price With Shipping","TCG Low Price","Total Quantity","Photo URL"]
    new_cards_df = new_cards_df.assign(**{col: '' for col in new_cols})
    new_cards_df["Product Line"] = new_cards_df["Product Line"].replace('', 'Magic')
    return new_cards_df

def add_inventory_and_change_headers():
    email_cards_file_path = EmailToCSV()
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
    inventory_filename = 'inventory.csv'
    inventory = pd.read_csv(inventory_filename)
    inventory = pd.concat([inventory, new_cards_df], ignore_index=True)
    inventory.to_csv(inventory_filename, index = False)

    new_cards_df = new_cards_df.rename(columns={"Quantity":"Add to Quantity","Name":"Product Name","Set":"Set Name","SKU":"TCGplayer Id","Price Each":"TCG Marketplace Price"})    
    new_cols = ["Title", "Number", "Rarity", "TCG Market Price","TCG Direct Low","TCG Low Price With Shipping","TCG Low Price","Total Quantity","Photo URL"]
    new_cards_df = new_cards_df.assign(**{"Product Line": "Magic"}, **{col: '' for col in new_cols})

    new_cards_df.to_csv(email_cards_file_path, index=False)


def update_inventory_and_sales(directory):
    shippingFileName = "_TCGplayer_ShippingExport"
    pullSheetFileName = "TCGplayer_PullSheet"
    pricingFileName = "TCGplayer__MyPricing"
    salesFileName = "sales.csv"
    inventoryFileName = 'inventory.csv'

    shippingFilePath = get_newest_file_matching_prefix(directory, shippingFileName)
    pullSheetFilePath = get_newest_file_matching_prefix(directory, pullSheetFileName)
    pricingFilePath = get_newest_file_matching_prefix(directory, pricingFileName)

    printFromCsv(shippingFilePath)

    cards_df = pd.read_csv(pullSheetFilePath)
    pricing_df = pd.read_csv(pricingFilePath)
    sales_df = pd.read_csv(salesFileName)
    inventory_df = pd.read_csv(inventoryFileName)

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
        
    inventory_df.to_csv(inventoryFileName, index=False)
    sales_df.to_csv(salesFileName, index=False)

    os.remove(shippingFilePath)
    os.remove(pullSheetFilePath)
    os.remove(pricingFilePath)

def remove_prices_under_10_cents():
    filePath = getFilePath()
    df = pd.read_csv(filePath)
    prices = df["Price Each"].str.replace('$','').astype(float)
    df.drop(df[prices < 0.1].index, inplace=True)
    df.to_csv(filePath, index=False)

def find_matching_cards():
    filePath1 = "inventory.csv"
    filePath2 = getFilePath()
    inventory = pd.read_csv(filePath1, index_col=0)
    findCards = pd.read_csv(filePath2, index_col=0)
    matches = inventory.merge(findCards, on="Name", how="inner")
    print(matches)

def merge_duplicates():
    csv_filename = getFilePath()
    df = pd.read_csv(csv_filename)
    df = df.groupby(['Product Name', 'Set Name', 'Printing', 'Condition', 'Language', 'TCGplayer Id', 'TCG Marketplace Price'], as_index=False)['Add to Quantity'].sum()
    df.to_csv(csv_filename, index=False)
    
def get_revenue():
    revenue_df = pd.read_csv("sales.csv")
    revenue_df['Date'] = pd.to_datetime(revenue_df['Date'])
    revenue_df = revenue_df[(revenue_df['Date'] > datetime.datetime(2022, 11, 13)) & (revenue_df['Date'] < datetime.datetime.now())]
    revenue_df = revenue_df.groupby('Lot')['Price'].sum()
    revenue_df = revenue_df.round(2)
    revenue_df.to_csv('revenue.csv', index=False, header=True)

def adjust_card_prices(flat_discount: float = 0, percentage: float = 1) -> None:
    """Change the prices of the cards in the CSV file"""
    prices_file_name = getFilePath()
    df = pd.read_csv(prices_file_name)
    df['TCG Marketplace Price'] = df.apply(lambda row: max(
        (get_clean_data(row["TCG Market Price"]) * percentage) - flat_discount - 0.01,
        get_clean_data(row["TCG Low Price"]) - .01,
        .01
    ), axis=1)
    df.to_csv(prices_file_name, index=False)

DIRECTORY = config.DOWNLOADS_DIRECTORY

commands = [
    {'text': 'Get cards from email then add to inventory then create email.csv', 'action': add_inventory_and_change_headers},
    {'text': 'Find and Print TCGPlayer Sales', 'action': lambda: update_inventory_and_sales(DIRECTORY)},
    {'text': 'Remove cards worth less than $0.10 market price from a selected file','action': remove_prices_under_10_cents},
    {'text': 'Find cards that are in a selected file and in "inventory.csv"','action': find_matching_cards},
    {'text': 'Combine duplicate cards in a selected file','action': merge_duplicates},
    {'text': 'Create "revenue.csv"','action': get_revenue},
    {'text': 'Change Prices','action': adjust_card_prices}
]

InputLoop(commands)
