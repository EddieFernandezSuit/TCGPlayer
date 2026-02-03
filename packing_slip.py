from PyPDF2 import PdfReader
import re
from collections import OrderedDict

class Order:
    def __init__(self, shipping_address, cards):
        self.shipping_address = shipping_address
        if shipping_address:
            self.name = shipping_address.split('\n')[0]
        else:
            self.name = None
        self.cards = cards
    
    def sort_cards(self):
        set_order = OrderedDict()
        for card in self.cards:
            if card.set_name not in set_order:
                set_order[card.set_name] = len(set_order)
        
        self.cards.sort(key=lambda card: (set_order[card.set_name], card.name))
    
    def print_order(self):
        print(self.name)
        for card in self.cards:
            print(f'{"\033[1m" if "foil" in card.condition else ""}{card.set_name} {card.quantity if card.quantity > 1 else ""} {card.name} {card.condition if card.condition != "Near Mint" else ""} {card.language if card.language != "English" else ""} ${card.price} {"\033[0m" if "foil" in card.condition else ""}')
        print()

class Card:
    def __init__(self, quantity, tcg_name, set_name, name, number, rarity,condition, price, total_price, language='English'):
        self.quantity = quantity
        self.tcg_name = tcg_name
        self.set_name = set_name
        self.name = name
        self.number = number
        self.rarity = rarity
        self.condition = condition
        self.price = price
        self.total_price = total_price
        self.language = language
        

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
    for page in reader.pages:
        text = page.extract_text()
        shipping_address = text.split('\nShip To',maxsplit=1)[0]
        raw_cards = get_between(text, 'Total Price\n', '\nTotal')
        if not raw_cards:
            continue
        raw_cards = re.split(r'\n(?=\d)', raw_cards)
        raw_cards = raw_cards[:-1]
        cards = []

        for raw_card in raw_cards:
            number = 0
            quantity, tcg_name, raw_card = raw_card.split(maxsplit=2)
            _, raw_card = raw_card.split('-',maxsplit=1)
            set_name, raw_card = raw_card.split(':',maxsplit=1)
            # print(raw_card)
            raw_card = raw_card.split('#', maxsplit=1)
            # print(raw_card)
            if len(raw_card) == 1:
                raw_card = raw_card[0]
                name, rarity, raw_card = raw_card.split('- ',maxsplit=2)
                
            else:
                name, raw_card = raw_card
                raw_card = raw_card.strip()
                raw_card = raw_card.split('- ', maxsplit=2)
                number, rarity, raw_card = raw_card
                number = number.strip()
            raw_card = raw_card.split('-')
            if len(raw_card) == 1:
                condition, price, total_price = raw_card[0].split('$')
                language = 'English'
            elif len(raw_card) == 2:
                token, raw_card = raw_card
                condition, price, total_price = raw_card.split('$')
            else:
                condition, language, raw_card = raw_card
                _, price, total_price = raw_card.split('$')

            set_name = set_name.strip()
            name = name.strip()
            condition = condition.strip()
            price = price.strip()
            
            card = Card(quantity, tcg_name, set_name, name, number, rarity, condition, price, total_price, language)
            cards.append(card)

        order = Order(shipping_address, cards)
        if shipping_address.startswith('Quantity'):
            orders[-1].cards += cards
        else:
            orders.append(order)
    
    for order in orders:
        order.sort_cards()

    return orders

