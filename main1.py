from mtgsdk import Card
from urllib.request import urlopen
from datetime import date
from PrintEnvelopes.getFilePath import getFilePath
from PrintEnvelopes.printEnvelopes import printFromCsv
from edlib import InputLoop
from PrintEnvelopes.readGmail import EmailToCSV
from csv import DictReader
import datetime
import pandas as pd
import math
import pygame
import sys
import io
import os
import re
import csv
import numpy as np
# pyinstaller --onefile main.py

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

class Game:
    def __init__(self, filePath):
        pygame.init()
        self.SCREEN_WIDTH = 1600
        self.SCREEN_HEIGHT = 700
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.colors = Color()
        self.fontSize = 20
        self.myFont = pygame.font.SysFont("freesansbold", self.fontSize)
        start(self, filePath)
        while True:
            update(self)
            draw(self)
            self.clock.tick(60)

def start(game, filePath):
    game.MTGCards = []
    game.NUM_CARDS_ROW = 10
    game.filePath = filePath
    currentCardPricesFilePath = getFilePath()
    game.currentCardPricesDf = pd.read_csv(currentCardPricesFilePath)
    os.remove(currentCardPricesFilePath)

def draw(game):
    game.screen = pygame.display.set_mode((game.SCREEN_WIDTH, game.SCREEN_HEIGHT))
    game.screen.fill(game.colors.GREY)
    xDistance = 155
    yDistance = 300
    ySperation = 15
    cardAttributes = ['quantity', 'lot', 'name', 'set', 'condition']
    cardAttributesShort = ['Qty: ', 'Lot: ', '', '', '']
    for i in range(min(game.NUM_CARDS_ROW, len(game.MTGCards))):
        for j in range(len(cardAttributes)):
            drawText(game, cardAttributesShort[j]  + str(game.MTGCards[i][cardAttributes[j]]), ySperation + xDistance * i, ySperation * (j + 1))
        game.screen.blit(game.MTGCards[i]['image'], (ySperation + xDistance * i, ySperation * (len(cardAttributesShort) + 1)))
    
    if len(game.MTGCards) > game.NUM_CARDS_ROW:
        for i in range(game.NUM_CARDS_ROW, len(game.MTGCards)):
            for j in range(len(cardAttributes)):
                drawText(game, cardAttributesShort[j] + str(game.MTGCards[i][cardAttributes[j]]), ySperation + xDistance * (i - game.NUM_CARDS_ROW), ySperation * (j + 1) + yDistance)
            game.screen.blit(game.MTGCards[i]['image'], (ySperation + xDistance * (i - game.NUM_CARDS_ROW), ySperation * (len(cardAttributesShort) + 1) + yDistance))
    pygame.display.update()

def update(game):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            os.remove(game.filePath)
            sys.exit()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            print("Finding Cards")
            shipType = 'normal'
        
            for j in range(game.NUM_CARDS_ROW * 2):
                newCards = pd.read_csv(game.filePath)
                for column in newCards.columns:
                    if column == 'Card Name' or column == 'Product Name':
                        if column == 'Card Name':
                            shipType = 'direct'
                        newCards = newCards.rename(columns={column: 'Name'})
                    elif column == 'Set Name':
                        newCards = newCards.rename(columns={column: 'Set'})

                if len(newCards.index) <= 0 or newCards["Quantity"][0] != newCards["Quantity"][0]:
                    print('Complete')
                    break

                MTGCard = {
                    'name': newCards["Name"][0],
                    'set': newCards["Set"][0],
                    'condition': newCards["Condition"][0],
                    'quantity': int(newCards["Quantity"][0])
                }

                for x in range(MTGCard['quantity']):
                    inventory = pd.read_csv("inventory.csv")
                    newCards.loc[0, "Quantity"] = str(int(MTGCard['quantity']) - 1)
                    index = None
                    for i in range(len(inventory["Name"])):
                        if inventory["Name"][i] == MTGCard['name'] and inventory["Set"][i] == MTGCard['set']:
                            if MTGCard['condition'][-4:] == "Foil":
                                if inventory["Foil"][i] == "Foil":
                                    index = i
                            else:
                                if inventory["Condition"][i] == MTGCard['condition']:
                                    index = i
                    if index == None:
                        price = 0
                        MTGCard['lot'] = -1
                    else:
                        inventory.loc[index, "Quantity"] = str(int(inventory["Quantity"][index]) - 1)
                        currentCardPricesDf = game.currentCardPricesDf
                        # price = float(currentCardPricesDf["TCG Marketplace Price"])
                        inventoryCondition = inventory["Condition"][index]
                        if inventory["Foil"][index] == "Foil":
                            inventoryCondition += " Foil"
                        if inventory["Language"][index] != "English":
                            inventoryCondition += " - " + inventory["Language"][index]
                        # priceIndex = np.where(currentCardPricesDf["Product Name"] == inventory["Name"][index] and currentCardPricesDf["Set Name"] == inventory["Set"][index] and currentCardPricesDf["Condition"] == inventoryCondition)[0][0]
                        # priceIndex = currentCardPricesDf.loc[(currentCardPricesDf["Product Name"] == inventory["Name"][index]) & (currentCardPricesDf["Set Name"] == inventory["Set"][index]) & (currentCardPricesDf["Condition"] == inventoryCondition)]
                        df = currentCardPricesDf[currentCardPricesDf["Product Name"] == inventory["Name"][index]]
                        df = df[df["Set Name"] == inventory["Set"][index]]
                        df = df[df["Condition"] == inventoryCondition]
                        cardIndex = df.index.values[0]
                        price = float(currentCardPricesDf["TCG Marketplace Price"][cardIndex])
                        # price = float(currentCardPricesDf["TCG Marketplace Price"][priceIndex])
                        # price = float(inventory["Price"][index][1:])
                        MTGCard['lot'] = int(math.floor(float(inventory["Lot"][index])))
                        if int(inventory["Quantity"][index]) <= 0:
                            inventory = inventory.drop([index])
                    
                    newRow = {'Name': MTGCard['name'], 'Set': MTGCard['set'], 'Condition': MTGCard['condition'], 'Lot': MTGCard['lot'],
                                'Price': price, 'Date': date.today(), 'shipType': shipType}
                    
                    salesFileName = "sales.csv"
                    sales = pd.read_csv(salesFileName)
                    sales = pd.concat([sales, pd.DataFrame.from_records([newRow])])
                    sales.to_csv(salesFileName, index=False)
                    inventory.to_csv("inventory.csv", index=False)
                
                # MTGCard['image'] = get_image(MTGCard['name'], MTGCard['set'])
                newCards = newCards.drop([0])
                newCards.to_csv(game.filePath, index=False)
                # game.MTGCards.append(MTGCard)
                if len(game.MTGCards) > game.NUM_CARDS_ROW * 2:
                    game.MTGCards.pop(0)
                draw(game)

def fixData():
    sales = pd.read_csv("sales.csv")
    for i, price in enumerate(sales["Price"]):
        if math.isnan(price):
            sales['Price'][i] = 0
    inv = pd.DataFrame(sales)
    inv.to_csv('sales.csv', index = False, header=True)

def getProf():
    sales = pd.read_csv("sales.csv")
    profits = {}
    highestLotNumber = 79

    for x in range(-1, highestLotNumber):
        profits[str(x)] = 0

    for x in sales.index:
        greaterThanDate = datetime.datetime(2022, 11, 13)
        now = datetime.datetime.now()
        date = datetime.datetime.strptime(sales["Date"][x], "%Y-%m-%d")
        if greaterThanDate < date and date < now:
            profits[str(int(sales["Lot"][x]))] += float(sales["Price"][x])
    
    allData = []
    for key in profits:
        data = {}
        data['Lot'] = key
        data['Profit'] = round(profits[key], 2)
        allData.append(data)

    dfProfits = pd.DataFrame(allData)
    dfProfits.to_csv('profits.csv', index=False, header=True)

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
    csvFile = pd.read_csv(filePath)
    csvFile = csvFile.rename(columns={"Quantity":"Add to Quantity","Name":"Product Name","Set":"Set Name","SKU":"TCGplayer Id","Price Each":"TCG Marketplace Price"})
    
    def addEmptyColumns(csvFile, arr):
        emptyColumn = []
        for x in csvFile.index:
            emptyColumn.append('')
        for x in arr:
            csvFile[x] = emptyColumn

    addEmptyColumns(csvFile, ["Product Line", "Title", "Number", "Rarity", "TCG Market Price","TCG Direct Low","TCG Low Price With Shipping","TCG Low Price","Total Quantity","Photo URL"])
    for x in csvFile.index:
        csvFile["Product Line"][x] = 'Magic'
        if csvFile["Printing"][x] != 'Normal':
            csvFile["Condition"][x] += ' ' + csvFile["Printing"][x]

        if csvFile["Language"][x] != 'English':
            csvFile["Condition"][x] += ' - ' + csvFile["Language"][x]
        csvFile["TCG Marketplace Price"][x] = csvFile["TCG Marketplace Price"][x][1:]
    
    csvFile.to_csv(filePath, index = False)

def addLot(lotStr, filePath):
    csvFile = pd.read_csv(filePath)

    newColumn = []
    for x in csvFile.index:
        newColumn.append(lotStr) 
        # print(csvFile['Name'][x])
        # print(csvFile["Quantity"][x])
        # print(csvFile["Set"][x])
        # print(csvFile["Printing"][x])
        # print(csvFile["Condition"][x])
        # print(csvFile["Language"][x])
        # print(csvFile["SKU"][x])
        # print(csvFile["Price Each"][x])
        csvFile["Price Each"][x] = '$' + str((float(csvFile["Price Each"][x][1:]) * 1))
    csvFile["Lot"] = newColumn

    inventory = pd.read_csv("inventory.csv")
    for x in csvFile.index:
        newRow = {'Quantity': csvFile["Quantity"][x], 'Name': csvFile["Name"][x], 'Set': csvFile["Set"][x], 'Foil': csvFile["Printing"][x],
            'Condition': csvFile["Condition"][x], 'Language': csvFile["Language"][x], 'SKU': csvFile["SKU"][x], 'Price': csvFile["Price Each"][x], "Lot": csvFile["Lot"][x]}
        # inventory = inventory.append(newRow, ignore_index=True)
        inventory = pd.concat([inventory, pd.DataFrame([newRow])], ignore_index=True)
    inventory.to_csv("inventory.csv", index = False)
    csvFile.to_csv(filePath, index = False)

def removeUnder10Cents():
    filePath = getFilePath()
    csvFile = pd.read_csv(filePath)
    for x in csvFile.index:
        if float(csvFile["Price Each"][x][1:]) < .1:
            csvFile = csvFile.drop([x])
    csvFile.to_csv(filePath, index = False)

def get_image(card_name, set_name):
    """Get the image of a card from the gatherer website."""
    card_name = removeParentheses(card_name).rstrip()
    set_name = removeParentheses(set_name).rstrip()
    print(set_name)
    print(card_name)
    print(type(card_name))
    print(type(set_name))
    cards = Card.where(name=card_name).all()
    print(cards)
    image_url = "http://gatherer.wizards.com/Handlers/Image.ashx?multiverseid=491806&type=card"

    for card in cards:
        if card.set_name == set_name:
            image_url = card.image_url if card.image_url is not None else image_url
            break

    image_str = urlopen(image_url).read()
    image_file = io.BytesIO(image_str)  # create a file object (stream)
    image = pygame.image.load(image_file)
    image = pygame.transform.scale(image, (150, 210))
    return image

def drawText(game, text, x, y):
    game.screen.blit(game.myFont.render(str(text), 1, game.colors.BLACK),(x, y))

def findIn(filePath1, filePath2):
    inventory = pd.read_csv(filePath1)
    findCards = pd.read_csv(filePath2)
    for x in findCards.index:
        sum = 0
        for y in inventory.index:
            if inventory["Name"][y] == findCards["Name"][x]:
                sum += int(inventory["Quantity"][y])
        print(str(sum) + " " + findCards["Name"][x])

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
    if data == '' :
        return 1000
    else:
        return float(data)

def change_prices():
    """Change the prices of the cards in the csv file"""
    flat_discount = 0
    percent_discount = 1
    csv_filename = getFilePath()
    dict_list = []
    with open(csv_filename, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            dict_list.append(row)
    
    for row in dict_list:
        # tcg_low_with_shipping = get_clean_data(row['TCG Low Price With Shipping'])
        tcg_low = get_clean_data(row['TCG Low Price'])
        market_price = get_clean_data(row['TCG Market Price'])
        row['TCG Marketplace Price'] = max((market_price * percent_discount) - flat_discount, tcg_low - .01, .01)
    
    with open(csv_filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=dict_list[0].keys())
        writer.writeheader()
        writer.writerows(dict_list)

def remove_lot_2():
    sales = pd.read_csv('sales.csv')
    sales.drop('Lot', inplace=True, axis = 1)
    sales = sales.rename(columns={'Lot2': 'Lot'})
    sales.to_csv("sales.csv", index=False)

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
    game = Game(pullSheetFilePath)

def FindCardsInNewAndInventory():
    fileName = getFilePath()
    findIn("inventory.csv",fileName)

def SortCSVByReleaseDate(filePath):
    newCardsdf = pd.read_csv(filePath)
    newCardsdf['Set Release Date'] = pd.to_datetime(newCardsdf['Set Release Date'])
    newCardsdf = newCardsdf.sort_values(by=['Set Release Date'], ascending=False)
    print(newCardsdf)
    newCardsdf.to_csv(filePath, index = False)

def GetLastFile(dir_path, file_name_prefix):
    lastFile = None
    # Iterate through all the files in the directory
    for file in os.listdir(dir_path):
        # Check if the file name starts with the input prefix
        if file.startswith(file_name_prefix):
            # Return the full path of the file
            lastFile = os.path.join(dir_path, file)
    # If no file was found, return None
    return lastFile

DIRECTORY = "C:\\Users\\Eddie\\Downloads"

commands = [
    {'text': 'Get cards from email then add to inventory then create email.csv', 'action': AddInvetoryAndChangeHeaders,},
    {'text': 'Find and Print TCGPlayer Sales', 'action': lambda: FindAndPrintTCGPlayerSales(DIRECTORY)},
    {'text': 'Remove cards worth less than $0.10 market price from a selected file','action': removeUnder10Cents},
    {'text': 'Find cards that are in a selected file and in "inventory.csv"','action': FindCardsInNewAndInventory},
    {'text': 'Combine duplicate cards in a selected file','action': combine_and_sum_quantity},
    {'text': 'Remove Lot 2 from selected file and Fix Headers','action': remove_lot_2},
    {'text': 'Calculate "profits.csv"','action': getProf},
    {'text': 'Change Prices','action': change_prices}
]
InputLoop(commands)