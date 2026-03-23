import pandas as pd
import pytest
from constants import DOWNLOADS_DIRECTORY


def calculate_price(row):
    PERCENT = 1
    FLAT_DISCOUNT = -0.05
    MIN = 0.03

    if pd.isna(row['TCG Market Price']) or pd.isna(row['TCG Low Price']):
        price = 100
    else:
        price = max(float(row['TCG Market Price']), float(row['TCG Low Price']))

    DIRECT = False

    if DIRECT:
        if price < 3:
            price = price * 2
        elif price < 20:
            price = price + 1.27
        elif price < 250:
            price = price + 4.17
        else:
            price = price + 7.5

    price = round(max((price * PERCENT) - FLAT_DISCOUNT, MIN), 2)
    return price


def make_row(market_price, low_price):
    """Helper to build a minimal row dict."""
    return {"TCG Market Price": market_price, "TCG Low Price": low_price}


# ── Unit tests ────────────────────────────────────────────────────────────────

def test_normal_uses_max_of_market_and_low():
    # market > low → uses market + 0.05 discount applied
    row = make_row(1.00, 0.50)
    assert calculate_price(row) == round(1.00 + 0.05, 2)

def test_normal_uses_low_when_greater():
    row = make_row(0.50, 1.00)
    assert calculate_price(row) == round(1.00 + 0.05, 2)

def test_flat_discount_adds_five_cents():
    # FLAT_DISCOUNT = -0.05, so subtracting it adds 0.05
    row = make_row(2.00, 2.00)
    assert calculate_price(row) == 2.05

def test_minimum_price_enforced():
    # Very low prices should floor at MIN (0.03)
    row = make_row(0.00, 0.00)
    assert calculate_price(row) == 0.03

def test_minimum_not_applied_above_floor():
    row = make_row(0.50, 0.50)
    assert calculate_price(row) > 0.03

def test_missing_market_price_returns_100_plus_discount():
    row = make_row(None, 0.50)
    assert calculate_price(row) == round(100 + 0.05, 2)

def test_missing_low_price_returns_100_plus_discount():
    row = make_row(1.00, None)
    assert calculate_price(row) == round(100 + 0.05, 2)

def test_both_missing_returns_100_plus_discount():
    row = make_row(None, None)
    assert calculate_price(row) == round(100 + 0.05, 2)

def test_nan_values():
    row = make_row(float("nan"), float("nan"))
    assert calculate_price(row) == round(100 + 0.05, 2)

def test_high_value_card():
    row = make_row(500.00, 490.00)
    assert calculate_price(row) == round(500.00 + 0.05, 2)

def test_result_is_rounded_to_two_decimals():
    row = make_row(1.111, 1.111)
    result = calculate_price(row)
    assert result == round(result, 2)

def test_equal_market_and_low():
    row = make_row(5.00, 5.00)
    assert calculate_price(row) == 5.05


# ── Integration test against real CSV ────────────────────────────────────────

def test_calculate_price_on_real_data():

    df = pd.read_csv(DOWNLOADS_DIRECTORY + "TCGplayer__MyPricing_20260310_071149.csv", dtype=str)
    prices = df.apply(calculate_price, axis=1)

    assert len(prices) == len(df),         "Should return a price for every row"
    assert (prices >= 0.03).all(),         "No price should be below MIN (0.03)"
    assert prices.notna().all(),           "No NaN prices in output"
    assert (prices == prices.round(2)).all(), "All prices rounded to 2 decimal places"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])