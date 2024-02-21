from datetime import date
from PrintEnvelopes.getFilePath import getFilePath
from PrintEnvelopes.printEnvelopes import printFromCsv
from edlib import InputLoop
from PrintEnvelopes.readGmail import EmailToCSV
import datetime
import pandas as pd
import math
import os
import re
import csv
import config
import numpy

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

def update_inventory_and_sales(filePath):
    currentCardPricesFilePath = getFilePath()
    salesFileName = "sales.csv"
    inventoryFileName = 'inventory.csv'

    newCards = pd.read_csv(filePath)
    currentCardPricesDf = pd.read_csv(currentCardPricesFilePath)
    sales = pd.read_csv(salesFileName)
    inventory = pd.read_csv(inventoryFileName)

    shipType = 'direct' if 'Card Name' in newCards.columns else 'normal'

    newCards = newCards.rename(columns={
        'Card Name': 'Name',
        'Set Name': 'Set',
        'Product Name': 'Name'
    })

    for j in range(len(newCards.index) - 1):
        quantity = int(newCards["Quantity"][j])

        salesNewRow = {
            'Name': newCards["Name"][j],
            'Set': newCards["Set"][j],
            'Condition': newCards['Condition'][j],
            'Lot': -1,
            'Price': 0,
            'Date': date.today(),
            'ShipType': shipType
        }

        newCardisFoil = newCards['Condition'][j][-4:] == "Foil"
        seperatedCondition = newCards['Condition'][j][:-5] if newCardisFoil else newCards["Condition"][j]
        seperatedFoil = "Foil" if newCardisFoil else "Normal"

        for _ in range(quantity):
            filteredCurrentCardPrices = currentCardPricesDf[(currentCardPricesDf["Product Name"] == salesNewRow['Name'])
                & (currentCardPricesDf["Set Name"] == salesNewRow['Set'])
                & (currentCardPricesDf["Condition"] == salesNewRow['Condition'])]
            
            if not filteredCurrentCardPrices.empty:
                salesNewRow['Price'] = float(filteredCurrentCardPrices["TCG Marketplace Price"].iloc[0])

            matchingRows = inventory.loc[(inventory["Name"] == salesNewRow['Name'])
                & (inventory["Set"] == salesNewRow['Set'])
                & (inventory["Condition"] == seperatedCondition)
                & (inventory["Foil"] == seperatedFoil)]
            
            if not matchingRows.empty:
                index = matchingRows.index[0]
                salesNewRow['Lot'] = int(inventory["Lot"][index])

                inventory.at[index, "Quantity"] -= 1

                if int(inventory["Quantity"][index]) == 0:
                    inventory = inventory.drop([index])

            sales = pd.concat([sales, pd.DataFrame.from_records([salesNewRow])])
        
    inventory.to_csv(inventoryFileName, index=False)
    sales.to_csv(salesFileName, index=False)

    os.remove(currentCardPricesFilePath)
    os.remove(filePath)
    print('Complete')

def fixData():
    sales = pd.read_csv("sales.csv")
    for i, price in enumerate(sales["Price"]):
        if math.isnan(price):
            sales['Price'][i] = 0
    inv = pd.DataFrame(sales)
    inv.to_csv('sales.csv', index = False, header=True)

def replace(addCards):
    addCards["Name"] = addCards["Name"].str.replace(' - C', '')
    addCards["Name"] = addCards["Name"].str.replace(' - L', '')
    addCards["Name"] = addCards["Name"].str.replace(' - R', '')
    addCards["Name"] = addCards["Name"].str.replace(' - U', '')
    addCards["Name"] = addCards["Name"].str.replace(' - T', '')
    for x in reversed(range(500)):
        temp = ' - #' + str(x)
        addCards["Name"] = addCards["Name"].str.replace(temp, '')

# def orderSets():
#     filePath = getFilePath()
#     newCards = pd.read_csv(filePath)
#     setOrder = pd.read_csv("setOrder.csv")

#     setOrderRows = setOrder.index
#     newCardsRows = newCards.index

#     for x in setOrderRows:
#         for y in newCardsRows:
#             if newCards['Set'][y] == setOrder['Set'][x]:
#                 newRow = {'Product Line': newCards['Product Line'][y], 'Product Name': newCards['Product Name'][y], 'Condition': newCards['Condition'][y], 'Number': newCards['Number'][y],
#                                 'Set': newCards['Set'][y], 'Rarity': newCards['Rarity'][y], 'Quantity': newCards['Quantity'][y], 'Main Photo URL': newCards['Main Photo URL'][y]}
#                 newCards = newCards.append(newRow, ignore_index=True)

#     for x in newCardsRows:
#         newCards = newCards.drop([x])

#     newCards.to_csv(filePath, index=False)

def removeParentheses(str):
    return re.sub(r"\([^()]*\)", "", str)

def newHeaders(filePath):
    df = pd.read_csv(filePath)
    df = df.rename(columns={"Quantity":"Add to Quantity","Name":"Product Name","Set":"Set Name","SKU":"TCGplayer Id","Price Each":"TCG Marketplace Price"}, inplace=True)
    
    new_cols = ["Product Line", "Title", "Number", "Rarity", "TCG Market Price","TCG Direct Low","TCG Low Price With Shipping","TCG Low Price","Total Quantity","Photo URL"]
    df = df.assign(**{k:'' for k in new_cols})

    df["Product Line"] = df["Product Line"].apply(lambda x: 'Magic' if x == '' else x)
    df["Condition"] = df["Condition"].apply(lambda x: x.strip() + ' ' + df["Printing"] if df["Printing"] != 'Normal' else x.strip())
    df["Condition"] = df["Condition"].apply(lambda x: x.strip() + ' - ' + df["Language"] if df["Language"] != 'English' else x.strip())
    df["TCG Marketplace Price"] = df["TCG Marketplace Price"].apply(lambda x: x.strip('$'))

    df.to_csv(filePath, index=False)

def addLot(lotStr, filePath):
    newCardsDf = pd.read_csv(filePath)
    inventory = pd.read_csv("inventory.csv")

    for x in newCardsDf.index:
        newCardsDf["Price Each"][x] = float(newCardsDf["Price Each"][x].strip("$"))
        newRow = {
            'Quantity': newCardsDf['Quantity'][x],
            'Name': newCardsDf['Name'][x],
            'Set': newCardsDf['Set'][x],
            'Foil': newCardsDf['Printing'][x],
            'Condition': newCardsDf['Condition'][x],
            'Language': newCardsDf['Language'][x],
            'SKU': newCardsDf['SKU'][x],
            'Price': newCardsDf['Price Each'][x],
            'Lot': lotStr
        }

        inventory = pd.concat([inventory, pd.DataFrame([newRow])], ignore_index=True)
    inventory.to_csv("inventory.csv", index = False)

def remove_prices_under_10_cents():
    filePath = getFilePath()
    df = pd.read_csv(filePath)
    prices = df["Price Each"].strip('$').astype(float)
    df.drop(df[prices < 0.1].index, inplace=True)
    df.to_csv(filePath, index=False)

def combine_and_sum_quantity():
    csv_filename = getFilePath()
    # create a dictionary to store the combined quantities for each unique data value
    combined = {}
    formattedCombined = []
    final_combined = [['Add to Quantity', 'Product Name', 'Set Name', 'Printing', 'Condition', 'Language', 'TCGplayer Id', 'TCG Marketplace Price']]
    type = 1

    with open(csv_filename, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            quantity = 'Add to Quantity'
            key = ''
            if type == 0:
                key = row['Name'] + '-' + row['Set'] + '-' + row['Printing'] + '-' + row['Condition'] + '-' + row['Language'] + '-' + row['SKU'] + '-10000'
            else:
                key = row['Product Name'] + '-' + row['Set Name'] + '-' + row['Printing'] + '-' + row['Condition'] + '-' + row['Language'] + '-' + row['TCGplayer Id'] + '-' + row['TCG Marketplace Price']
            if key in combined:
                combined[key] += int(row[quantity])
            else:
                combined[key] = int(row[quantity])
        for key in combined:
            splitData = key.split('-')
            formattedCombined.append({
                'Add to Quantity': combined[key],
                'Product Name': splitData[0],
                'Set Name': splitData[1],
                'Printing': splitData[2],
                'Condition': splitData[3],
                'Language': splitData[4],
                'TCGplayer Id': splitData[5],
                'TCG Marketplace Price': splitData[6],
            })
        for item in formattedCombined:
            final_combined.append([item['Add to Quantity'], item['Product Name'], item['Set Name'], item['Printing'], item['Condition'], item['Language'], item['TCGplayer Id'], item['TCG Marketplace Price']])
    with open(csv_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(final_combined)
    return final_combined
    
def get_clean_data(data):
    return 0.01 if math.isnan(data) or data == '' else float(data)


def AddInvetoryAndChangeHeaders():
    emailCSVFilePath = EmailToCSV()
    lotNumber = input('Enter Lot number: ')
    addLot(lotNumber, emailCSVFilePath)
    newHeaders(emailCSVFilePath)

def FindAndPrintTCGPlayerSales(directory):
    shippingFileName = "_TCGplayer_ShippingExport"
    shippingFilePath = GetLastFile(directory, shippingFileName)
    printFromCsv(shippingFilePath)
    os.remove(shippingFilePath)
    pullSheetFileName = "TCGplayer_PullSheet"
    pullSheetFilePath = GetLastFile(directory, pullSheetFileName)
    pd.set_option("display.max_columns", 9)
    update_inventory_and_sales(pullSheetFilePath)

def find_matching_cards():
    filePath1 = "inventory.csv"
    filePath2 = getFilePath()
    inventory = pd.read_csv(filePath1, index_col=0)
    findCards = pd.read_csv(filePath2, index_col=0)
    matches = inventory.merge(findCards, on="Name", how="inner")
    print(matches)

def SortCSVByReleaseDate(filePath):
    newCardsdf = pd.read_csv(filePath)
    newCardsdf['Set Release Date'] = pd.to_datetime(newCardsdf['Set Release Date'])
    newCardsdf = newCardsdf.sort_values(by=['Set Release Date'], ascending=False)
    print(newCardsdf)
    newCardsdf.to_csv(filePath, index = False)

def GetLastFile(dir_path, file_name_prefix):
    lastFile = None
    for file in os.listdir(dir_path):
        if file.startswith(file_name_prefix):
            lastFile = os.path.join(dir_path, file)
    return lastFile

def get_revenue():
    revenue_df = pd.read_csv("sales.csv")
    revenue_df['Date'] = pd.to_datetime(revenue_df['Date'])
    revenue_df = revenue_df[(revenue_df['Date'] > datetime.datetime(2022, 11, 13)) & (revenue_df['Date'] < datetime.datetime.now())]
    revenue_df = revenue_df.groupby('Lot')['Price'].sum()
    revenue_df = revenue_df.round(2)
    revenue_df = revenue_df.reset_index()
    revenue_df.to_csv('revenue2.csv', index=False, header=True)

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
    {'text': 'Get cards from email then add to inventory then create email.csv', 'action': AddInvetoryAndChangeHeaders},
    {'text': 'Find and Print TCGPlayer Sales', 'action': lambda: FindAndPrintTCGPlayerSales(DIRECTORY)},
    {'text': 'Remove cards worth less than $0.10 market price from a selected file','action': remove_prices_under_10_cents},
    {'text': 'Find cards that are in a selected file and in "inventory.csv"','action': find_matching_cards},
    {'text': 'Combine duplicate cards in a selected file','action': combine_and_sum_quantity},
    {'text': 'Create "revenue.csv"','action': get_revenue},
    {'text': 'Change Prices','action': adjust_card_prices}
]

InputLoop(commands)

