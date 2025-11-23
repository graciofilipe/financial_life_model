import pytest
from financial_life.uk_gov import TaxMan
from financial_life.investments_and_savings import GeneralInvestmentAccount, StocksAndSharesISA, PensionAccount, FixedInterest

@pytest.fixture
def tax_man():
    """Returns a TaxMan instance with standard 2025/26 defaults."""
    return TaxMan()

@pytest.fixture
def empty_gia():
    """Returns an empty General Investment Account."""
    return GeneralInvestmentAccount(initial_value=0, initial_units=0, initial_average_buy_price=0)

@pytest.fixture
def funded_gia():
    """Returns a GIA with 100 units bought at £1.00 each (Value £100)."""
    return GeneralInvestmentAccount(initial_value=100, initial_units=100, initial_average_buy_price=1.0)

@pytest.fixture
def pension_pot():
    """Returns a Pension Account with £100,000."""
    return PensionAccount(initial_value=100000)
