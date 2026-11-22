"""Tests for the duplicate merging in packing_slip.all_cards.

The block exercised in test_main_flow_... is copied verbatim from main.py:

    orders = get_orders_from_pdf(PACKING_SLIP_PATH)
    all_cards(orders)

    for order in orders:
        order.print_order()
        input('')

get_orders_from_pdf is monkeypatched because it needs a real TCGPlayer PDF.
"""

import csv

import pytest

import packing_slip
from packing_slip import Card, Order, ProductIdResolver, resolve_product_ids


def make_card(quantity, set_name, name, condition='Near Mint', language='English', price='0.25'):
    return Card(quantity, 'TCGPlayer', set_name, name, '', 'Common', condition, price, '0.00', language)


def make_order(name, cards):
    return Order(f'{name}\n1 Main St', cards)


def test_duplicate_quantities_are_summed_across_orders(capsys):
    orders = [
        make_order('Alice', [make_card('1', 'Sword & Shield', 'Darkrai'),
                             make_card('2', 'Sword & Shield', 'Pikachu')]),
        make_order('Bob', [make_card('3', 'Sword & Shield', 'Darkrai')]),
    ]

    packing_slip.all_cards(orders)

    out = capsys.readouterr().out
    assert '4 Darkrai' in out
    assert '2 Pikachu' in out


def test_all_cards_does_not_mutate_source_orders(capsys):
    orders = [
        make_order('Alice', [make_card('1', 'Sword & Shield', 'Darkrai')]),
        make_order('Bob', [make_card('3', 'Sword & Shield', 'Darkrai')]),
    ]

    packing_slip.all_cards(orders)

    assert [card.quantity for card in orders[0].cards] == ['1']
    assert [card.quantity for card in orders[1].cards] == ['3']


def test_main_flow_prints_each_order_with_its_own_quantities(monkeypatch, capsys):
    orders = [
        make_order('Alice', [make_card('2', 'Sword & Shield', 'Darkrai')]),
        make_order('Bob', [make_card('2', 'Sword & Shield', 'Darkrai')]),
    ]
    monkeypatch.setattr(packing_slip, 'get_orders_from_pdf', lambda filepath: orders)
    monkeypatch.setattr('builtins.input', lambda *args: '')

    orders = packing_slip.get_orders_from_pdf('packing-slip.pdf')
    packing_slip.all_cards(orders)

    for order in orders:
        order.print_order()
        input('')

    _, _, per_order = capsys.readouterr().out.partition('All Cards')
    _, _, rest = per_order.partition('Alice')
    alice, _, bob = rest.partition('Bob')

    assert '2 Darkrai' in alice
    assert '4 Darkrai' not in alice
    assert '2 Darkrai' in bob
    assert '4 Darkrai' not in bob


def test_duplicates_within_a_single_order_are_merged(capsys):
    orders = [
        make_order('Alice', [make_card('2', 'Sword & Shield', 'Zoroa'),
                             make_card('1', 'Sword & Shield', 'Zoroa')]),
    ]

    packing_slip.all_cards(orders)

    out = capsys.readouterr().out
    assert '3 Zoroa' in out
    assert out.count('Zoroa') == 1


def test_same_name_in_different_sets_stays_separate(capsys):
    orders = [
        make_order('Alice', [make_card('2', 'Sword & Shield', 'Darkrai')]),
        make_order('Bob', [make_card('3', 'Lost Caverns', 'Darkrai')]),
    ]

    packing_slip.all_cards(orders)

    out = capsys.readouterr().out
    assert '5 Darkrai' not in out
    assert out.count('Darkrai') == 2


def test_foil_and_non_foil_stay_separate(capsys):
    orders = [
        make_order('Alice', [make_card('1', 'Sword & Shield', 'Darkrai')]),
        make_order('Bob', [make_card('1', 'Sword & Shield', 'Darkrai', condition='Near Mint Foil')]),
    ]

    packing_slip.all_cards(orders)

    out = capsys.readouterr().out
    assert '2 Darkrai' not in out
    assert out.count('Darkrai') == 2


def test_language_is_part_of_identity_and_survives_the_merge(capsys):
    orders = [
        make_order('Alice', [make_card('1', 'Sword & Shield', 'Yugi', language='Japanese')]),
        make_order('Bob', [make_card('1', 'Sword & Shield', 'Yugi', language='Japanese')]),
    ]

    packing_slip.all_cards(orders)

    out = capsys.readouterr().out
    assert out.count('Yugi') == 1
    assert 'Japanese' in out


def test_cards_without_duplicates_pass_through_unchanged(capsys):
    orders = [
        make_order('Alice', [make_card('1', 'Sword & Shield', 'Darkrai'),
                             make_card('1', 'Tempest', 'Bolt')]),
    ]

    packing_slip.all_cards(orders)

    out = capsys.readouterr().out
    assert [line for line in out.splitlines() if line.strip()] == [
        'All Cards',
        'Sword & Shield:  Darkrai   $0.25 ',
        'Tempest:  Bolt   $0.25 ',
    ]


def test_merged_cards_keep_set_first_appearance_order_and_sort_names(capsys):
    orders = [
        make_order('Alice', [make_card('1', 'Zendikar', 'Bolt'),
                             make_card('1', 'Alpha', 'Yugi'),
                             make_card('1', 'Zendikar', 'Ambush')]),
    ]

    packing_slip.all_cards(orders)

    out = capsys.readouterr().out
    sets = [line.split(':')[0] for line in out.splitlines() if ':' in line]
    assert sets == ['Zendikar', 'Zendikar', 'Alpha']
    assert out.index('Ambush') < out.index('Bolt')


def test_get_orders_from_pdf_keeps_full_set_names_and_clean_card_names(monkeypatch):
    page_text = """Ship To:
Sample Buyer
1001 Example St
Quantity
Description
Price
Total Price
1
Pokemon - SV: Black Bolt: Genesect ex - #067/086 - Double Rare - 
Near Mint Holofoil
$1.02
$1.02
1
Magic - The Hobbit: Eternal-Legal: Galadriel's Dismissal 
(Borderless) - #16 - R - Near Mint Foil
$40.24
$40.24
1
Total
$41.26
"""

    class Page:
        def extract_text(self):
            return page_text

    class Reader:
        def __init__(self, filepath):
            self.pages = [Page()]

    monkeypatch.setattr(packing_slip, 'PdfReader', Reader)

    orders = packing_slip.get_orders_from_pdf('packing-slip.pdf')

    assert len(orders) == 1
    genesect, galadriel = orders[0].cards
    assert (genesect.set_name, genesect.name, genesect.number) == (
        'SV: Black Bolt', 'Genesect ex', '067/086'
    )
    assert (galadriel.set_name, galadriel.name, galadriel.number) == (
        'The Hobbit: Eternal-Legal', "Galadriel's Dismissal (Borderless)", '16'
    )


def make_pokemon_card(product_id=None, **kwargs):
    return Card(
        '1', 'Pokemon', 'SV: Black Bolt', 'Genesect ex', '067/086', 'Double Rare',
        'Near Mint Holofoil', '0.65', '0.65', product_id=product_id, **kwargs
    )


def test_direct_product_url_has_no_search_query():
    card = make_pokemon_card(product_id='642518')

    assert card.get_tcgplayer_url() == (
        'https://store.tcgplayer.com/admin/product/manage/642518'
    )


def test_product_id_from_photo_url_is_used_for_direct_url():
    card = make_pokemon_card(
        photo_url='https://tcgplayer-cdn.tcgplayer.com/product/559647_in_200x200.jpg'
    )

    assert card.product_id == '559647'
    assert card.get_tcgplayer_url() == (
        'https://store.tcgplayer.com/admin/product/manage/559647'
    )


def test_url_falls_back_to_search_when_no_product_id_is_known():
    card = make_pokemon_card()

    url = card.get_tcgplayer_url()

    assert url.startswith('https://store.tcgplayer.com/admin/product/manage?')
    assert 'SearchValue=Genesect%20ex' in url


def test_all_cards_keeps_product_id_when_merging(capsys):
    orders = [
        make_order('Alice', [make_pokemon_card(product_id='642518')]),
        make_order('Bob', [make_pokemon_card(product_id='642518')]),
    ]

    packing_slip.all_cards(orders)

    out = capsys.readouterr().out
    assert '2 Genesect ex' in out


def search_result(product_id, number='067/086', rarity='Double Rare'):
    return {
        'productId': float(product_id),
        'productName': 'Genesect ex',
        'setName': 'SV: Black Bolt',
        'rarityName': rarity,
        'customAttributes': {'number': number},
    }


def test_resolver_chooses_the_matching_number(tmp_path):
    calls = []

    def search(card):
        calls.append(card)
        return [
            search_result('111111', number='001/086'),
            search_result('642518', number='067/086'),
        ]

    resolver = ProductIdResolver(cache_path=str(tmp_path / 'ids.csv'), search=search)

    assert resolver.resolve_card(make_pokemon_card()) == '642518'
    assert len(calls) == 1


def test_resolver_retries_alternate_set_name_splits_for_colon_names(tmp_path):
    card = Card(
        '1', 'Magic', 'Ice Age: Circle of Protection', 'Red', '1', 'Common',
        'Near Mint', '0.25', '0.25',
        description='Ice Age: Circle of Protection: Red',
    )

    def search(candidate):
        if (candidate.set_name, candidate.name) != ('Ice Age', 'Circle of Protection: Red'):
            return []
        return [{
            'productId': float('1687'),
            'productName': 'Circle of Protection: Red',
            'setName': 'Ice Age',
            'rarityName': 'Common',
            'customAttributes': {'number': '1'},
        }]

    resolver = ProductIdResolver(cache_path=str(tmp_path / 'ids.csv'), search=search)

    assert resolver.resolve_card(card) == '1687'
    assert (card.set_name, card.name) == ('Ice Age', 'Circle of Protection: Red')


def test_resolver_returns_none_when_results_are_ambiguous(tmp_path):
    def search(card):
        return [
            search_result('111111', number='067/086'),
            search_result('222222', number='067/086'),
        ]

    resolver = ProductIdResolver(cache_path=str(tmp_path / 'ids.csv'), search=search)

    assert resolver.resolve_card(make_pokemon_card()) is None


def test_resolver_returns_none_when_search_fails(tmp_path):
    def search(card):
        raise OSError('offline')

    resolver = ProductIdResolver(cache_path=str(tmp_path / 'ids.csv'), search=search)

    assert resolver.resolve_card(make_pokemon_card()) is None


def test_resolver_reads_and_writes_the_cache(tmp_path):
    cache_path = tmp_path / 'ids.csv'
    resolver = ProductIdResolver(
        cache_path=str(cache_path),
        search=lambda card: [search_result('642518')],
    )
    assert resolver.resolve_card(make_pokemon_card()) == '642518'

    with open(cache_path, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    assert rows == [{
        'name': 'genesect ex',
        'set_name': 'sv black bolt',
        'number': '67/86',
        'rarity': 'double rare',
        'product_id': '642518',
    }]

    second_resolver = ProductIdResolver(
        cache_path=str(cache_path),
        search=lambda card: pytest.fail('cache should be used instead of searching'),
    )
    assert second_resolver.resolve_card(make_pokemon_card()) == '642518'


def test_resolve_product_ids_updates_every_card(tmp_path):
    orders = [
        make_order('Alice', [make_pokemon_card(), make_pokemon_card()]),
    ]
    resolver = ProductIdResolver(
        cache_path=str(tmp_path / 'ids.csv'),
        search=lambda card: [search_result('642518')],
    )

    assert resolve_product_ids(orders, resolver=resolver) == 2
    for card in orders[0].cards:
        assert card.product_id == '642518'
        assert card.tcgplayer_id == 642518


def test_print_order_omits_hyperlinks_when_output_is_not_a_terminal(monkeypatch, capsys):
    order = make_order('Alice', [make_pokemon_card(product_id='642518')])
    original_stdout = packing_slip.sys.stdout

    class NotATerminal:
        def isatty(self):
            return False

        def write(self, text):
            return original_stdout.write(text)

        def flush(self):
            return original_stdout.flush()

    monkeypatch.setattr(packing_slip.sys, 'stdout', NotATerminal())
    order.print_order()

    out = capsys.readouterr().out
    assert 'Genesect ex' in out
    assert '\033]8;;' not in out


def test_print_order_emits_hyperlinks_on_a_terminal(monkeypatch):
    order = make_order('Alice', [make_pokemon_card(product_id='642518')])
    output = []

    class Terminal:
        def isatty(self):
            return True

        def write(self, text):
            output.append(text)

        def flush(self):
            return None

    monkeypatch.setattr(packing_slip.sys, 'stdout', Terminal())
    order.print_order()

    printed = ''.join(output)
    assert (
        '\033]8;;https://store.tcgplayer.com/admin/product/manage/642518\033\\'
        in printed
    )
