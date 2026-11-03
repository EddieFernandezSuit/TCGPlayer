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
    
    def print_order(self, open_urls=False, interactive=False, open_by_index=False, open_card_names=False):
        import sys
        import os
        if webbrowser is None:
            import webbrowser as _wb
            webbrowser_mod = _wb
        else:
            webbrowser_mod = webbrowser

        def open_card_url(card):
            try:
                if webbrowser_mod:
                    webbrowser_mod.open(card.get_tcgplayer_url())
            except Exception:
                pass

        def make_hyperlink(text, url):
            try:
                if os.environ.get('NO_HYPERLINKS') or os.environ.get('PACKING_SLIP_NO_FORMAT'):
                    return text
                return f'\033]8;;{url}\033\\{text}\033]8;;\033\\'
            except Exception:
                return text

        print(self.name)
        for i, card in enumerate(self.cards, 1):
            name_text = card.name.replace("-", "")
            name_display = make_hyperlink(name_text, card.get_tcgplayer_url()) if not open_card_names else name_text
            try:
                qty_float = float(card.quantity) if card.quantity is not None else 0
                qty_int = int(qty_float) if qty_float.is_integer() else qty_float
                quantity_str = str(qty_int)
            except Exception:
                try:
                    qty_float = 0
                    quantity_str = str(card.quantity) if card.quantity is not None else ''
                except Exception:
                    qty_float = 0
                    quantity_str = ''
            if qty_float > 1:
                qty_display = quantity_str + ' '
            else:
                qty_display = ' '
            line = f'{"\033[1m" if "foil" in card.condition else ""}{card.set_name}: {qty_display}{name_display} {card.condition if card.condition != "Near Mint" else ""} {card.language if card.language != "English" else ""} {"$" + card.price if float(card.price) > .1 else ""} {"\033[0m" if "foil" in card.condition else ""}'
            if interactive:
                try:
                    print(line, end='', flush=True)
                    response = input('')
                    r = response.strip()
                    rl = r.lower()
                    if rl == 'q':
                        print()
                        return
                    if rl == 'o' or rl == '':
                        if rl == 'o':
                            open_card_url(card)
                        print()
                    elif r.isdigit():
                        idx = int(r) - 1
                        if 0 <= idx < len(self.cards):
                            open_card_url(self.cards[idx])
                        print()
                    else:
                        print()
                except (EOFError, KeyboardInterrupt):
                    print()
                    break
            else:
                print(line)
                if open_urls:
                    open_card_url(card)
        if open_by_index:
            try:
                response = input('Enter index to open (blank to skip): ')
                if response.strip().isdigit():
                    idx = int(response.strip()) - 1
                    if 0 <= idx < len(self.cards):
                        open_card_url(self.cards[idx])
            except (EOFError, KeyboardInterrupt):
                pass
        print()

import re
try:
    import webbrowser
except Exception:
    webbrowser = None

class Card:
    def __init__(self, quantity, tcg_name, set_name, name, number, rarity,condition, price, total_price, language='English', tcgplayer_id=None, product_id=None, photo_url=None):
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
        self.tcgplayer_id = tcgplayer_id
        self.product_id = product_id
        self.photo_url = photo_url
        if not self.product_id and self.photo_url:
            m = re.search(r'/product/(\d+)', str(self.photo_url))
            if m:
                self.product_id = m.group(1)
        if not self.tcgplayer_id and self.product_id:
            try:
                self.tcgplayer_id = int(self.product_id)
            except Exception:
                pass

    def get_tcgplayer_url(self):
        from urllib.parse import quote
        base = 'https://store.tcgplayer.com/admin/product/manage'
        if self.product_id:
            base = f'{base}/{self.product_id}'
        elif self.tcgplayer_id:
            base = f'{base}/{self.tcgplayer_id}'
        return f'{base}?OnlyMyInventory=false&SearchValue={quote(self.name)}&CategoryId=0&SetNameId=0&Rarity=0&DidSearch=true'

    def open_url(self):
        if webbrowser is None:
            try:
                import webbrowser as _wb
                _wb.open(self.get_tcgplayer_url())
                return
            except Exception:
                pass
        try:
            webbrowser.open(self.get_tcgplayer_url())
        except Exception:
            pass

    def key(self):
        return (self.set_name, self.name, self.condition, self.language)
        

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
            number, rarity = '', ''
            try:
                number = 0
                quantity, tcg_name, raw_card = raw_card.split(maxsplit=2)
                _, raw_card = raw_card.split('-',maxsplit=1)
                set_name, raw_card = raw_card.split(':',maxsplit=1)
                raw_card = raw_card.split('#', maxsplit=1)
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
            except Exception as e:
                print(e)
                print(f'Raw Card: {raw_card}, Number: {number}, Rarity: {rarity}')

        order = Order(shipping_address, cards)
        if shipping_address.startswith('Quantity'):
            orders[-1].cards += cards
        else:
            orders.append(order)
    
    for order in orders:
        order.sort_cards()

    return orders

# combines all cards from all orders into one order, merging duplicates by summing quantity,
# and prints it, sorted by set and then name
def all_cards(orders: list[Order]):
    merged = OrderedDict()
    for order in orders:
        for card in order.cards:
            key = card.key()
            if key not in merged:
                merged[key] = Card(card.quantity, card.tcg_name, card.set_name, card.name, card.number, card.rarity, card.condition, card.price, card.total_price, card.language)
            else:
                quantity = int(merged[key].quantity) + int(card.quantity)
                merged[key].quantity = str(quantity)
                merged[key].total_price = f'{quantity * float(merged[key].price):.2f}'

    order = Order('All Cards', list(merged.values()))
    order.sort_cards()
    order.print_order()
