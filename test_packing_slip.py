"""Tests for the duplicate merging in packing_slip.all_cards.

The block exercised in test_main_flow_... is copied verbatim from main.py:

    orders = get_orders_from_pdf(PACKING_SLIP_PATH)
    all_cards(orders)

    for order in orders:
        order.print_order()
        input('')

get_orders_from_pdf is monkeypatched because it needs a real TCGPlayer PDF.
"""

import pytest

import packing_slip
from packing_slip import Card, Order


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
