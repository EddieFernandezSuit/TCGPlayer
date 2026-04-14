# TODO: Fix create_magic_sorter_inventory_file function

**Status: Done**

## Steps:
1. [x] Add null-check in proccess_new_cards_magic_sorter(): if pricing is None, skip or error.
2. [x] Edit main.py: Fix function scoping/logic per plan (per-row extraction, correct keys 'Total Quantity'/'Product Name'/'Set Name'/'Number', safe int).
3. [x] Test: Run proccess_new_cards_magic_sorter(), verify interesting.csv.
4. [x] Complete.

