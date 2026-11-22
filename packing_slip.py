from PyPDF2 import PdfReader
import copy
import csv
import json
import os
import re
import sys
import urllib.request
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
                # Only emit terminal hyperlinks when writing to a terminal. Captured or
                # redirected output stays plain text so logs and tests remain readable.
                if not sys.stdout.isatty():
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
    def __init__(self, quantity, tcg_name, set_name, name, number, rarity,condition, price, total_price, language='English', tcgplayer_id=None, product_id=None, photo_url=None, description=None):
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
        self.description = description
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
        product_id = self.product_id or self.tcgplayer_id
        if product_id:
            return f'{base}/{product_id}'
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
        

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PRODUCT_ID_CACHE = os.path.join(BASE_DIR, 'data', 'product_ids.csv')
TCGPLAYER_SEARCH_URL = 'https://mp-search-api.tcgplayer.com/v1/search/request'


def _normalize_text(value):
    text = str(value or '').strip().lower()
    text = text.replace('\u2019', "'")
    text = re.sub(r'[^a-z0-9/]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def _normalize_number(value):
    text = str(value or '').strip().lower()
    if not text:
        return ''
    parts = []
    for part in text.split('/'):
        part = part.strip()
        if part.isdigit():
            parts.append(str(int(part)))
        else:
            parts.append(re.sub(r'[^a-z0-9]+', '', part))
    return '/'.join(parts)


def _normalize_product_id(value):
    text = str(value or '').strip()
    if not text:
        return ''
    try:
        number = float(text)
    except ValueError:
        match = re.search(r'/product/(\d+)', text)
        return match.group(1) if match else ''
    if number.is_integer() and number > 0:
        return str(int(number))
    return ''


class ProductIdResolver:
    """Resolve TCGplayer product IDs from packing-slip card details.

    IDs are looked up in a small CSV cache first and then through TCGplayer's
    public search endpoint. When a card cannot be resolved confidently, callers
    should keep the existing search URL as a fallback.
    """

    def __init__(self, cache_path=None, search=None):
        self.cache_path = cache_path or DEFAULT_PRODUCT_ID_CACHE
        self._search_func = search or self._search_tcgplayer
        self._cache = None
        self._memo = {}
        self._search_failed = False

    def _key_for(self, set_name, name, number, rarity):
        return (
            _normalize_text(name),
            _normalize_text(set_name),
            _normalize_number(number),
            _normalize_text(rarity),
        )

    def _candidate_pairs(self, card):
        """Return possible (set, name) splits for an ambiguous description."""
        pairs = [(card.set_name, card.name)]
        description = getattr(card, 'description', None)
        if description:
            parts = description.split(':')
            for index in range(1, len(parts)):
                set_name = ':'.join(parts[:index]).strip()
                name = ':'.join(parts[index:]).strip()
                pair = (set_name, name)
                if set_name and name and pair not in pairs:
                    pairs.append(pair)
        return pairs

    def _load_cache(self):
        if self._cache is not None:
            return
        self._cache = {}
        try:
            with open(self.cache_path, newline='', encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    product_id = str(row.get('product_id') or '').strip()
                    if not product_id.isdigit():
                        continue
                    key = (
                        _normalize_text(row.get('name')),
                        _normalize_text(row.get('set_name')),
                        _normalize_number(row.get('number')),
                        _normalize_text(row.get('rarity')),
                    )
                    self._cache[key] = product_id
        except (OSError, csv.Error):
            pass

    def _save_cache(self):
        if self._cache is None:
            return
        try:
            cache_dir = os.path.dirname(self.cache_path)
            if cache_dir:
                os.makedirs(cache_dir, exist_ok=True)
            with open(self.cache_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f, fieldnames=['name', 'set_name', 'number', 'rarity', 'product_id']
                )
                writer.writeheader()
                for key, product_id in sorted(self._cache.items()):
                    name, set_name, number, rarity = key
                    writer.writerow({
                        'name': name,
                        'set_name': set_name,
                        'number': number,
                        'rarity': rarity,
                        'product_id': product_id,
                    })
        except OSError:
            pass

    def _search_tcgplayer(self, card):
        term = {'productName': [card.name]}
        if card.set_name:
            term['setName'] = [card.set_name]
        payload = {
            'algorithm': 'sales_synonym_v2',
            'from': 0,
            'size': 24,
            'filters': {'term': term, 'range': {}, 'match': {}},
            'listingSearch': {
                'context': {'cart': {}},
                'filters': {
                    'term': {'sellerStatus': 'Live', 'channelId': 0},
                    'range': {'quantity': {'gte': 1}},
                    'exclude': {'channelExclusion': 0},
                },
            },
            'context': {'cart': {}, 'shippingCountry': 'US', 'userProfile': {}},
        }
        request = urllib.request.Request(
            TCGPLAYER_SEARCH_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0',
            },
            method='POST',
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.load(response)

        results = []
        for group in data.get('results') or []:
            results.extend(group.get('results') or [])
        return results

    def _score_result(self, card, result):
        if not _normalize_product_id(result.get('productId')):
            return None

        if _normalize_text(result.get('productName')) != _normalize_text(card.name):
            return None

        score = 10

        wanted_set = _normalize_text(card.set_name)
        result_set = _normalize_text(result.get('setName'))
        if wanted_set:
            if result_set == wanted_set:
                score += 5
            elif wanted_set in result_set or result_set in wanted_set:
                score += 2
            else:
                return None

        wanted_number = _normalize_number(card.number)
        if wanted_number in ('', '0'):
            wanted_number = ''
        result_number = _normalize_number(
            (result.get('customAttributes') or {}).get('number')
        )
        if wanted_number and result_number:
            if result_number == wanted_number:
                score += 6
            else:
                return None

        wanted_rarity = _normalize_text(card.rarity)
        result_rarity = _normalize_text(result.get('rarityName'))
        if wanted_rarity and result_rarity:
            score += 3 if result_rarity == wanted_rarity else -1

        return score

    def _choose_product_id(self, card, results):
        scored = []
        for result in results:
            score = self._score_result(card, result)
            if score is not None:
                scored.append((score, _normalize_product_id(result.get('productId'))))
        if not scored:
            return None

        best_score = max(score for score, _ in scored)
        best_ids = {product_id for score, product_id in scored if score == best_score}
        if len(best_ids) == 1:
            return best_ids.pop()
        return None

    def resolve_card(self, card):
        existing_id = _normalize_product_id(card.product_id or card.tcgplayer_id)
        if existing_id:
            return existing_id

        self._load_cache()
        for set_name, name in self._candidate_pairs(card):
            key = self._key_for(set_name, name, card.number, card.rarity)
            if key in self._memo:
                product_id = self._memo[key]
            else:
                product_id = self._cache.get(key)
                if not product_id:
                    candidate = copy.copy(card)
                    candidate.set_name = set_name
                    candidate.name = name
                    if self._search_failed:
                        results = []
                    else:
                        try:
                            results = self._search_func(candidate)
                        except Exception:
                            # Stop searching after a connection/rate-limit failure so
                            # an offline run does not wait on every single card.
                            self._search_failed = True
                            results = []
                    product_id = self._choose_product_id(candidate, results)
                    if product_id:
                        self._cache[key] = product_id
                        self._save_cache()
                self._memo[key] = product_id

            if product_id:
                card.set_name = set_name
                card.name = name
                card.description = f'{set_name}: {name}'
                return product_id
        return None

    def resolve_cards(self, cards):
        resolved = 0
        for card in cards:
            product_id = self.resolve_card(card)
            if not product_id:
                continue
            if not card.product_id:
                card.product_id = product_id
            if not card.tcgplayer_id:
                try:
                    card.tcgplayer_id = int(product_id)
                except (TypeError, ValueError):
                    pass
            resolved += 1
        return resolved


def resolve_product_ids(orders, resolver=None):
    """Attach resolved TCGplayer product IDs to every card in ``orders``."""
    resolver = resolver or ProductIdResolver()
    return resolver.resolve_cards(
        card for order in orders for card in order.cards
    )


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
                description = None
                if '#' in raw_card:
                    description = raw_card.split('#', maxsplit=1)[0]
                    description = re.sub(r'\s*-\s*$', '', description)
                    description = re.sub(r'\s+', ' ', description).strip()
                # Set names can contain colons (e.g. "SV: Black Bolt"), so split on
                # the last colon to keep the full set name and only the card name.
                set_name, raw_card = raw_card.rsplit(':',maxsplit=1)
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
                name = re.sub(r'\s*-\s*$', '', name)
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

                set_name = re.sub(r'\s+', ' ', set_name).strip()
                name = re.sub(r'\s+', ' ', name).strip()
                rarity = re.sub(r'\s+', ' ', rarity).strip()
                condition = re.sub(r'\s+', ' ', condition).strip()
                language = re.sub(r'\s+', ' ', language).strip()
                price = price.strip()
                total_price = total_price.strip()
                
                card = Card(quantity, tcg_name, set_name, name, number, rarity, condition, price, total_price, language, description=description)
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
                merged[key] = Card(
                    card.quantity, card.tcg_name, card.set_name, card.name, card.number,
                    card.rarity, card.condition, card.price, card.total_price, card.language,
                    tcgplayer_id=card.tcgplayer_id, product_id=card.product_id,
                    photo_url=card.photo_url, description=card.description,
                )
            else:
                quantity = int(merged[key].quantity) + int(card.quantity)
                merged[key].quantity = str(quantity)
                merged[key].total_price = f'{quantity * float(merged[key].price):.2f}'
                if not merged[key].product_id and card.product_id:
                    merged[key].product_id = card.product_id
                if not merged[key].tcgplayer_id and card.tcgplayer_id:
                    merged[key].tcgplayer_id = card.tcgplayer_id

    order = Order('All Cards', list(merged.values()))
    order.sort_cards()
    order.print_order()
