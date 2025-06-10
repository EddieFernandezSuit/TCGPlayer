from PyPDF2 import PdfReader
import re
from collections import OrderedDict
from pprint import pprint


class Order:
    def __init__(self, shipping_address, cards):
        self.shipping_address = shipping_address
        if shipping_address:
            self.name = shipping_address.split('\n')[0]
        else:
            self.name = None
        self.cards = cards
        # for card in cards:
        #     print(card.__dict__)
        # self.sort_cards_by_first_seen_set_order()
        # for card in cards: print(card.__dict__)
    
    def sort_cards(self):
        # Capture the order of first appearance of each set_name
        set_order = OrderedDict()
        for card in self.cards:
            if card.set_name not in set_order:
                set_order[card.set_name] = len(set_order)
        
        # Sort cards using the index of their set_name in set_order
        self.cards.sort(key=lambda card: set_order[card.set_name])
    
    def print_order(self):
        # print(order.shipping_address)
        print(self.name)
        for card in self.cards:
            print(card.quantity + ' ' + card.set_name + '   ' + card.name + ' ' + card.condition + ' ' + card.price)
        print()

class Card:
    def __init__(self, quantity, tcg_name, set_name, name, number, rarity,condition, price, total_price):
        self.quantity = quantity
        self.tcg_name = tcg_name
        self.set_name = set_name
        self.name = name
        self.number = number
        self.rarity = rarity
        self.condition = condition
        self.price = price
        self.total_price = total_price
        

def get_between(text, before_string, after_string):
    between_text = text.split(before_string, 1)
    if len(between_text) == 1:
        return None
    between_text = between_text[1]
    between_text = between_text.split(after_string, 1)[0]
    return between_text


def get_orders_from_pdf(filepath):
    orders = []
    reader = PdfReader(filepath)
    number_of_pages = len(reader.pages)
    for page in reader.pages:
        text = page.extract_text()
        shipping_address = text.split('\nShip To',maxsplit=1)[0]
        # shipping_address = get_between(text, 'Ship To:\n', '\nOrder Number:')
        raw_cards = get_between(text, 'Total Price\n', '\nTotal')
        # raw_cards = raw_cards[:-1]
        if not raw_cards:
            continue
        raw_cards = re.split(r'\n(?=\d)', raw_cards)
        # if 'Total' in raw_cards[-1]:
        raw_cards = raw_cards[:-1]
        cards = []

        for raw_card in raw_cards:
            quantity, tcg_name, raw_card = raw_card.split(maxsplit=2)
            _, raw_card = raw_card.split('-',maxsplit=1)
            set_name, raw_card = raw_card.split(':',maxsplit=1)
            raw_card = raw_card.split('#', maxsplit=1)
            if len(raw_card) == 1:
                raw_card = raw_card[0]
                name, raw_card = raw_card.split('-',maxsplit=1)
            else:
                name, raw_card = raw_card
                number, rarity, raw_card = raw_card.split('-')
            condition, price, total_price = raw_card.split('$')

            set_name = set_name.strip()
            name = name.strip()
            number = number.strip()
            condition = condition.strip()
            price = price.strip()
            
            card = Card(quantity, tcg_name, set_name, name, number, rarity, condition, price, total_price)
            cards.append(card)

        order = Order(shipping_address, cards)
        if not shipping_address:
            orders[-1].cards += cards
        else:
            orders.append(order)
    
    for order in orders:
        order.sort_cards()

    return orders

# orders = get_orders_from_pdf("C:\\Users\\ferna\\Downloads\\TCGplayer_PackingSlips_20250509_145736.pdf")
# for order in orders:
#     order.print_order()
#     input('')


