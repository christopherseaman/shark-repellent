import math

def test_format_p_value_small():
    from datasci.pvalues import format_p_value
    assert format_p_value(0.00001) == "< 0.0001"

def test_format_p_value_normal():
    from datasci.pvalues import format_p_value
    assert format_p_value(0.0234) == "0.0234"

def test_format_p_value_nan():
    from datasci.pvalues import format_p_value
    assert format_p_value(float("nan")) == "N/A"

def test_is_significant_true():
    from datasci.pvalues import is_significant
    assert is_significant(0.01, 0.05) is True

def test_is_significant_false():
    from datasci.pvalues import is_significant
    assert is_significant(0.10, 0.05) is False
