import pytest
from financial_life.human import generate_salary, generate_living_costs, Human

def test_salary_growth():
    """Test salary grows by rate until plateau."""
    salary_map = generate_salary(
        base_salary=10000,
        base_year=2024,
        growth_rate=0.10,
        last_work_year=2026,
        growth_stop_year=2025,
        post_plateau_growth_rate=0.0
    )
    
    # 2024: 10000 (Base)
    # 2025: 11000 (10% Growth)
    # 2026: 11000 (Plateaued)
    
    assert salary_map[2025] == pytest.approx(11000)
    assert salary_map[2026] == pytest.approx(11000)
    assert 2027 not in salary_map # Retired

def test_living_costs_lifestyling():
    """Test costs change rate after retirement and slow down."""
    costs = generate_living_costs(
        base_cost=10000,
        base_year=2024,
        rate_pre_retirement=0.0,
        rate_post_retirement=0.10,
        retirement_year=2026,
        final_year=2028,
        one_off_expenses={"2027": 5000},
        slow_down_year=2028,
        rate_post_slow_down=0.0
    )
    
    # 2025 (Pre-Ret): 10000
    assert costs[2025] == 10000
    
    # 2026 (Retirement Year): Still uses pre-ret logic in current implementation
    assert costs[2026] == 10000
    
    # 2027: Grows by post-ret rate (10%) from 2026 base (10000 * 1.1 = 11000) + OneOff (5000) = 16000
    assert costs[2027] == pytest.approx(16000)
    
    # 2028 (Slow Down): Base (11000) grows by post-ret rate (11000 * 1.1 = 12100). 
    assert costs[2028] == pytest.approx(12100)

class TestHumanUtility:
    def test_buy_utility_diminishing_returns(self):
        # Mock draw_down_function
        dummy_draw_down = lambda pot, year, ret, final: 0
        h = Human(starting_cash=10000, living_costs={}, non_linear_utility=0.5, pension_draw_down_function=dummy_draw_down) # Sqrt utility
        
        h.buy_utility(100)
        # Utility = 100 ^ 0.5 = 10
        assert h.utility[-1] == 10.0
        assert h.cash == 9900

    def test_buy_utility_allows_overdraft(self):
        dummy_draw_down = lambda pot, year, ret, final: 0
        h = Human(starting_cash=50, living_costs={}, non_linear_utility=0.99, pension_draw_down_function=dummy_draw_down)
        
        # Try to buy 100, having only 50
        h.buy_utility(100)
        
        # Should spend 100 and go into overdraft
        # (Constraint logic is in the simulation loop, not the Human class)
        assert h.cash == -50
