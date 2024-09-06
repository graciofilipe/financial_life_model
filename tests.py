import unittest
from investments_and_savings import GeneralInvestmentAccount

class TestGeneralInvestmentAccount(unittest.TestCase):

    def setUp(self):
        self.gia = GeneralInvestmentAccount(initial_value=100, initial_units=100, growth_rate=0.01)

    def test_initial_values(self):
        self.gia = GeneralInvestmentAccount(initial_value=100, initial_units=100, growth_rate=0.01)
        self.assertEqual(self.gia.asset_value, 100)
        self.assertEqual(self.gia.growth_rate, 0.01)
        self.assertEqual(self.gia.units, 100)
        self.assertEqual(self.gia.average_unit_buy_price, 1)
        self.assertEqual(self.gia.current_unit_price, 1)

    def test_put_money(self):
 #       self.gia = GeneralInvestmentAccount(initial_value=100, initial_units=100, growth_rate=0.01)
        self.gia.put_money(50)
        self.assertAlmostEqual(self.gia.asset_value, 150)
        self.assertAlmostEqual(self.gia.units, 150)
        self.assertAlmostEqual(self.gia.average_unit_buy_price, 1)

    def test_get_money(self):
#        self.gia = GeneralInvestmentAccount(initial_value=100, initial_units=100, growth_rate=0.01)
        amount, capital_gains = self.gia.get_money(50)
        self.assertEqual(amount, 50)
        self.assertEqual(capital_gains, 0)  # No gains/losses when buying and selling at the same price
        self.assertEqual(self.gia.asset_value, 50)
        self.assertAlmostEqual(self.gia.units, 50)

    def test_get_money_insufficient_funds(self):
        result = self.gia.get_money(150)
        self.assertEqual(result, 0)
        self.assertEqual(self.gia.asset_value, 100)  # Ensure no money was withdrawn

    def test_grow_per_year(self):
        self.gia.grow_per_year()
        self.assertAlmostEqual(self.gia.asset_value, 101)
        self.assertAlmostEqual(self.gia.current_unit_price, 1.01)

    def test_grow_ten_years(self):
        self.gia.grow_per_year()#1
        self.gia.grow_per_year()#2
        self.gia.grow_per_year()#3
        self.gia.grow_per_year()#4
        self.gia.grow_per_year()#5
        self.gia.grow_per_year()#6
        self.gia.grow_per_year()#7
        self.gia.grow_per_year()#8
        self.gia.grow_per_year()#9
        self.gia.grow_per_year()#10
        self.assertEqual(self.gia.asset_value, 100*(1.01**10))
        self.assertEqual(self.gia.current_unit_price, 1*1.01**10)
        self.assertEqual(self.gia.units, 100)


    def test_grow_and_harvest(self):
        self.gia.grow_per_year()#1
        self.gia.grow_per_year()#2
        self.gia.grow_per_year()#3
        money_to_get = 10

        amount, capital_gains = self.gia.get_money(money_to_get)
        
        self.assertEqual(amount, money_to_get)  
        self.assertAlmostEqual(capital_gains, money_to_get - money_to_get/((1+self.gia.growth_rate)**3))

    def test_grow_per_year_zero_units(self):
        self.gia.units = 0
        self.gia.grow_per_year()
        self.assertEqual(self.gia.asset_value, 0)
        self.assertEqual(self.gia.units, 0)




from investments_and_savings import SotcksAndSharesISA

class TestSotcksAndSharesISA(unittest.TestCase):

    def setUp(self):
        self.isa = SotcksAndSharesISA(initial_value=100, growth_rate=0.01)

    def test_initial_values(self):
        self.assertEqual(self.isa.asset_value, 100)
        self.assertEqual(self.isa.growth_rate, 0.01)

    def test_put_money(self):
        self.isa.put_money(50)
        self.assertEqual(self.isa.asset_value, 150)

    def test_get_money_sufficient_funds(self):
        amount = self.isa.get_money(60)
        self.assertEqual(amount, 60)
        self.assertEqual(self.isa.asset_value, 40)

    def test_get_money_insufficient_funds(self):
        amount = self.isa.get_money(150)
        self.assertEqual(amount, 0)  # Should return 0 if insufficient funds
        self.assertEqual(self.isa.asset_value, 100)  # Ensure no money was withdrawn

    def test_grow_per_year(self):
        self.isa.grow_per_year()
        self.assertEqual(self.isa.asset_value, 101)




from investments_and_savings import PensionAccount

class TestPensionAccount(unittest.TestCase):

    def setUp(self):
        self.pension = PensionAccount(initial_value=100, growth_rate=0.01)

    def test_initial_values(self):
        self.assertEqual(self.pension.asset_value, 100)
        self.assertEqual(self.pension.growth_rate, 0.01)

    def test_put_money(self):
        self.pension.put_money(50)
        self.assertEqual(self.pension.asset_value, 150)

    def test_get_money_sufficient_funds(self):
        amount = self.pension.get_money(60)
        self.assertEqual(amount, 60)
        self.assertEqual(self.pension.asset_value, 40)

    def test_get_money_insufficient_funds(self):
        amount = self.pension.get_money(150)
        self.assertEqual(amount, 0)  # Should return 0 if insufficient funds
        self.assertEqual(self.pension.asset_value, 100)  # Ensure no money was withdrawn

    def test_grow_per_year(self):
        self.pension.grow_per_year()
        self.assertEqual(self.pension.asset_value, 101)






import unittest
from human import Human, Employment

class TestHuman(unittest.TestCase):

    def setUp(self):
        self.living_costs = {2024: 30000, 2025: 31000}
        self.pension_draw_down_function = lambda x,y,z,w: 10000  # Simple function for testing
        self.human = Human(starting_cash=50000, living_costs=self.living_costs, 
        pension_draw_down_function=self.pension_draw_down_function, non_linear_utility=0.5)

    def test_initial_values(self):
        self.assertEqual(self.human.cash, 50000)
        self.assertEqual(self.human.living_costs, self.living_costs)
        self.assertEqual(self.human.utility, [])

    def test_buy_utility(self):
        self.human.buy_utility(1000)
        self.assertEqual(self.human.cash, 49000)
        self.assertEqual(self.human.utility, [1000**self.human.non_linear_utility])

    def test_put_in_cash(self):
        self.human.put_in_cash(2000)
        self.assertEqual(self.human.cash, 52000)

    def test_get_from_cash_sufficient_funds(self):
        amount = self.human.get_from_cash(10000)
        self.assertEqual(amount, 10000)
        self.assertEqual(self.human.cash, 40000)

    def test_get_from_cash_insufficient_funds(self):
        amount = self.human.get_from_cash(60000)
        self.assertEqual(amount, 0)  # Should return 0 if insufficient funds
        self.assertEqual(self.human.cash, 50000)  # Ensure no money was withdrawn


class TestEmployment(unittest.TestCase):

    def setUp(self):
        self.gross_salary = {2024: 60000, 2025: 62000}
        self.employment = Employment(gross_salary=self.gross_salary, employee_pension_contributions_pct=0.07, employer_pension_contributions_pct=0.07)

    def test_get_salary_before_tax_after_pension_contributions(self):
        salary = self.employment.get_salary_before_tax_after_pension_contributions(2024)
        self.assertAlmostEqual(salary, 60000*(1-0.07))  # Gross salary minus pension contributions

    def test_get_gross_salary(self):
        salary = self.employment.get_gross_salary(2024)
        self.assertEqual(salary, 60000)

    def test_get_employee_pension_contributions(self):
        contribution = self.employment.get_employee_pension_contributions(2024)
        self.assertAlmostEqual(contribution, 60000 * 0.07)

    def test_get_employer_pension_contributions(self):
        contribution = self.employment.get_employer_pension_contributions(2024)
        self.assertAlmostEqual(contribution, 60000 * 0.07)




if __name__ == '__main__':
    unittest.main()
