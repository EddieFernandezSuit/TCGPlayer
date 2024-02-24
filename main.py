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

class Color:
    GREY = (150, 150, 150)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    CYAN = (0, 255, 255)
    PINK = (220, 20, 60)
    PURPLE = (138, 43, 226)
    ORANGE = (255, 165, 0)
    WHITE = (255, 255, 255)

def fix_data():
    sales = pd.read_csv("sales.csv")
    for i, price in enumerate(sales["Price"]):
        if math.isnan(price):
            sales['Price'][i] = 0
    inv = pd.DataFrame(sales)
    inv.to_csv('sales.csv', index = False, header=True)

def replace(addCards):
    for suffix in [' - C', ' - L', ' - R', ' - U', ' - T'] + [' - #' + str(x) for x in reversed(range(500))]:
        addCards["Name"] = addCards["Name"].str.replace(suffix, '')

def orderSets():
    filePath = getFilePath()
    newCards = pd.read_csv(filePath)
    setOrder = pd.read_csv("setOrder.csv")

    setOrderRows = setOrder.index
    newCardsRows = newCards.index

    for x in setOrderRows:
        for y in newCardsRows:
            if newCards['Set'][y] == setOrder['Set'][x]:
                newRow = {'Product Line': newCards['Product Line'][y], 'Product Name': newCards['Product Name'][y], 'Condition': newCards['Condition'][y], 'Number': newCards['Number'][y],
                                'Set': newCards['Set'][y], 'Rarity': newCards['Rarity'][y], 'Quantity': newCards['Quantity'][y], 'Main Photo URL': newCards['Main Photo URL'][y]}
                newCards = newCards.append(newRow, ignore_index=True)

    for x in newCardsRows:
        newCards = newCards.drop([x])

    newCards.to_csv(filePath, index=False)

def removeParentheses(str):
    return re.sub(r"\([^()]*\)", "", str)

def addLot(lotStr, filePath):
    newCardsDf = pd.read_csv(filePath)
    inventory = pd.read_csv("inventory.csv")
    newCardsDf["Price Each"] = newCardsDf["Price Each"].str.strip("$").astype(float)
    newCardsDf['Lot'] = lotStr
    inventory = pd.concat([inventory, newCardsDf], ignore_index=True)
    inventory.to_csv("inventory.csv", index = False)

def update_headers(filePath):
    df = pd.read_csv(filePath)
    df = df.rename(columns={"Quantity":"Add to Quantity","Name":"Product Name","Set":"Set Name","SKU":"TCGplayer Id","Price Each":"TCG Marketplace Price"}, inplace=True)
    new_cols = ["Product Line", "Title", "Number", "Rarity", "TCG Market Price","TCG Direct Low","TCG Low Price With Shipping","TCG Low Price","Total Quantity","Photo URL"]
    df = df.assign(**{k:'' for k in new_cols})
    df["Product Line"] = df["Product Line"].apply(lambda x: 'Magic' if x == '' else x)
    df["Condition"] = df["Condition"].apply(lambda x: x.strip() + ' ' + df["Printing"] if df["Printing"] != 'Normal' else x.strip())
    df["Condition"] = df["Condition"].apply(lambda x: x.strip() + ' - ' + df["Language"] if df["Language"] != 'English' else x.strip())
    df["TCG Marketplace Price"] = df["TCG Marketplace Price"].apply(lambda x: x.strip('$'))
    df.to_csv(filePath, index=False)

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

def add_inventory_and_change_headers():
    emailCSVFilePath = EmailToCSV()
    lotNumber = input('Enter Lot number: ')
    addLot(lotNumber, emailCSVFilePath)
    update_headers(emailCSVFilePath)

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


    shipType = 'direct' if 'Card Name' in cards_df.columns else 'normal'

    cards_df = cards_df.rename(columns={
        'Card Name': 'Name',
        'Set Name': 'Set',
        'Product Name': 'Name'
    })

    for j in range(len(cards_df.index) - 1 ):
        quantity = int(cards_df["Quantity"][j])

        salesNewRow = {
            'Name': cards_df["Name"][j],
            'Set': cards_df["Set"][j],
            'Condition': cards_df['Condition'][j],
            'Lot': -1,
            'Price': 0,
            'Date': datetime.date.today(),
            'ShipType': shipType
        }

        newCardisFoil = cards_df['Condition'][j][-4:] == "Foil"
        seperatedCondition = cards_df['Condition'][j][:-5] if newCardisFoil else cards_df["Condition"][j]
        seperatedFoil = "Foil" if newCardisFoil else "Normal"

        filteredCurrentCardPrices = pricing_df[(pricing_df["Product Name"] == salesNewRow['Name'])
            & (pricing_df["Set Name"] == salesNewRow['Set'])
            & (pricing_df["Condition"] == salesNewRow['Condition'])]
        
        for _ in range(quantity):
            if not filteredCurrentCardPrices.empty:
                salesNewRow['Price'] = float(filteredCurrentCardPrices["TCG Marketplace Price"].iloc[0])

            matchingRows = inventory_df.loc[(inventory_df["Name"] == salesNewRow['Name'])
                & (inventory_df["Set"] == salesNewRow['Set'])
                & (inventory_df["Condition"] == seperatedCondition)
                & (inventory_df["Foil"] == seperatedFoil)]
            
            if not matchingRows.empty:
                index = matchingRows.index[0]
                salesNewRow['Lot'] = int(inventory_df["Lot"][index])

                inventory_df.at[index, "Quantity"] -= 1

                if int(inventory_df["Quantity"][index]) == 0:
                    inventory_df = inventory_df.drop([index])

            sales_df = pd.concat([sales_df, pd.DataFrame.from_records([salesNewRow])])
        
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