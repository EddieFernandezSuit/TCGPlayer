from PrintEnvelopes.getFilePath import getFilePath
from csv import DictReader

def calcNewPrice(card):
    price = max(float(card['TCG Market Price']), float(card['TCG Low Price With Shipping']) - .99) * 1 - .01
    if  price < .01:
        price = .01
    print(price)
    return price

filePath = getFilePath()

with open(filePath, 'r') as f:
    dictReader = DictReader(f)
    cardData = list(dictReader)
    # print(cardData)

for card in cardData:
    card['TCG Marketplace Price'] = calcNewPrice(card)