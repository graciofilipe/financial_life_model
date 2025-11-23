import pytest

class TestGeneralInvestmentAccount:
    def test_initialization_with_values(self, funded_gia):
        assert funded_gia.asset_value == 100
        assert funded_gia.units == 100
        assert funded_gia.current_unit_price == 1.0
        assert funded_gia.average_unit_buy_price == 1.0

    def test_initialization_defaults(self, empty_gia):
        assert empty_gia.asset_value == 0
        assert empty_gia.units == 0
        assert empty_gia.current_unit_price == 1.0 # Default if empty

    def test_put_money_buys_units(self, empty_gia):
        # Price is 1.0 by default. Put £100.
        empty_gia.put_money(100)
        assert empty_gia.asset_value == 100
        assert empty_gia.units == 100
        assert empty_gia.average_unit_buy_price == 1.0

    def test_growth_updates_price_and_value(self, funded_gia):
        # Grow by 10%
        funded_gia.grow_per_year(0.10)
        assert funded_gia.current_unit_price == 1.10
        assert funded_gia.asset_value == pytest.approx(110.0)
        # Units shouldn't change
        assert funded_gia.units == 100

    def test_withdrawal_with_gains(self, funded_gia):
        # 1. Grow to £2.00/unit (100% gain)
        funded_gia.grow_per_year(1.00) 
        assert funded_gia.asset_value == 200
        
        # 2. Withdraw £100 (Should sell 50 units)
        # Cost basis for 50 units = 50 * £1 = £50
        # Sale proceeds = £100
        # Gain = £50
        amount, gains = funded_gia.get_money(100)
        
        assert amount == 100
        assert gains == 50
        assert funded_gia.units == 50
        assert funded_gia.asset_value == 100

    def test_averaging_down(self, empty_gia):
        # 1. Buy 100 units at £1.00
        empty_gia.put_money(100)
        
        # 2. Price drops to £0.50
        empty_gia.current_unit_price = 0.50
        empty_gia.asset_value = 50
        
        # 3. Buy £50 worth (100 units)
        empty_gia.put_money(50)
        
        # Total Units = 200.
        # Total Cost = £150.
        # Avg Price should be £0.75
        assert empty_gia.units == 200
        assert empty_gia.average_unit_buy_price == 0.75

    def test_insufficient_funds(self, funded_gia):
        amount, gains = funded_gia.get_money(200)
        assert amount == 0
        assert gains == 0


class TestPensionAccount:
    def test_growth_tax_free(self, pension_pot):
        pension_pot.grow_per_year(0.05)
        assert pension_pot.asset_value == 105000

    def test_contributions(self, pension_pot):
        pension_pot.put_money(10000)
        assert pension_pot.asset_value == 110000
