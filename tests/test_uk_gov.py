import pytest
from financial_life.uk_gov import TaxMan

class TestIncomeTax:
    def test_personal_allowance_only(self, tax_man):
        """Income within PA should be tax free."""
        assert tax_man.calculate_uk_income_tax(12570) == 0
        assert tax_man.calculate_uk_income_tax(5000) == 0

    def test_basic_rate(self, tax_man):
        """Income in basic band (12571 - 50270)."""
        # Income 50,000. Taxable = 50000 - 12570 = 37430.
        # Tax = 37430 * 0.20 = 7486
        assert tax_man.calculate_uk_income_tax(50000) == pytest.approx(7486.0)

    def test_higher_rate(self, tax_man):
        """Income in higher band (50271 - 125140)."""
        # Income 100,000. Taxable = 87430.
        # Basic band (37700 * 0.2) = 7540
        # Higher band (87430 - 37700 = 49730) * 0.4 = 19892
        # Total = 27432
        assert tax_man.calculate_uk_income_tax(100000) == pytest.approx(27432.0)

    def test_personal_allowance_taper(self, tax_man):
        """Income over 100k reduces PA by 1 for every 2."""
        # Income 120,000.
        # Excess = 20,000. Reduction = 10,000.
        # New PA = 2570.
        # Taxable = 117,430.
        # Basic (37700 * 0.2) = 7540
        # Higher (117430 - 37700 = 79730) * 0.4 = 31892
        # Total = 39432
        assert tax_man.calculate_uk_income_tax(120000) == pytest.approx(39432.0)

    def test_additional_rate(self, tax_man):
        """Income over 125140 (Additional Rate)."""
        # Income 150,000. PA is 0.
        # Taxable = 150,000.
        # Basic (37700 * 0.2) = 7540
        # Higher (125140 - 37700 = 87440) * 0.4 = 34976
        # Additional (150000 - 125140 = 24860) * 0.45 = 11187
        # Total = 53703
        assert tax_man.calculate_uk_income_tax(150000) == pytest.approx(53703.0)


class TestNationalInsurance:
    def test_below_threshold(self, tax_man):
        assert tax_man.calculate_uk_national_insurance(12570) == 0

    def test_basic_rate(self, tax_man):
        # Income 50,000.
        # Taxable NI = 50000 - 12570 = 37430
        # Rate 8% = 2994.4
        assert tax_man.calculate_uk_national_insurance(50000) == pytest.approx(2994.4)

    def test_upper_earnings_limit(self, tax_man):
        # Income 60,000.
        # Band 1 (12570 to 50270): 37700 * 0.08 = 3016
        # Band 2 (50270 to 60000): 9730 * 0.02 = 194.6
        # Total = 3210.6
        assert tax_man.calculate_uk_national_insurance(60000) == pytest.approx(3210.6)


class TestCapitalGainsTax:
    def test_allowance(self, tax_man):
        """Gains within allowance (3k) are tax free."""
        assert tax_man.capital_gains_tax_due(3000, total_taxable_income=50000) == 0

    def test_basic_rate_taxpayer(self, tax_man):
        """Basic rate taxpayer pays 18% on gains."""
        # Income 30k (Basic band). Gain 13k.
        # Taxable Gain = 10k.
        # Total Income 40k < 50k threshold -> All at 18%.
        # Tax = 1800.
        assert tax_man.capital_gains_tax_due(13000, total_taxable_income=30000) == pytest.approx(1800.0)

    def test_higher_rate_taxpayer(self, tax_man):
        """Higher rate taxpayer pays 24% on gains."""
        # Income 60k (Higher band). Gain 13k.
        # Taxable Gain = 10k.
        # Tax = 2400.
        assert tax_man.capital_gains_tax_due(13000, total_taxable_income=60000) == pytest.approx(2400.0)

    def test_tier_spillover(self, tax_man):
        """Gain pushes taxpayer from basic to higher band."""
        # Income 45,000. Threshold 50,270.
        # Headroom in basic band = 5,270.
        # Gain 13,000. Taxable = 10,000.
        # 5,270 taxed at 18% = 948.6
        # Remaining 4,730 taxed at 24% = 1135.2
        # Total = 2083.8
        assert tax_man.capital_gains_tax_due(13000, total_taxable_income=45000) == pytest.approx(2083.8)


class TestPensionTaper:
    def test_standard_allowance(self, tax_man):
        # Income below 200k threshold
        assert tax_man.pension_allowance(100000, 20000, 10000) == 60000

    def test_taper_activation(self, tax_man):
        # Threshold Income = 220k (>200k)
        # Adjusted Income = 220k + 40k (ER) = 260k.
        # At 260k adjusted, allowance is still 60k (start of taper).
        assert tax_man.pension_allowance(200000, 20000, 40000) == 60000

    def test_full_taper(self, tax_man):
        # Adjusted Income 360k.
        # Excess = 100k. Reduction = 50k.
        # Allowance = 60k - 50k = 10k (Min).
        assert tax_man.pension_allowance(300000, 20000, 40000) == 10000
