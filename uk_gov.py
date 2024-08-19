
class TaxMan:
    def __init__(self):
        pass

    def calculate_uk_income_tax(self, gross_income):
        """
        Calculates the amount of UK income tax due based on the provided gross income.

        Args:
            gross_income (float): The individual's total income before any deductions.

        Returns:
            float: The amount of income tax due.
        """

        # Personal Allowance
        personal_allowance = 12570

        # Check if Personal Allowance is reduced due to high income
        if gross_income > 100000:
            personal_allowance_reduction = (gross_income - 100000) / 2
            personal_allowance = max(0, personal_allowance - personal_allowance_reduction)

        # Taxable income
        taxable_income = max(0, gross_income - personal_allowance)

        # Tax bands and rates
        tax_bands = [
            (0, 0.0),        # Personal Allowance
            (50270, 0.2),     # Basic rate
            (125140, 0.4),    # Higher rate
            (float('inf'), 0.45)  # Additional rate
        ]

        # Calculate tax due
        tax_due = 0
        remaining_taxable_income = taxable_income

        for upper_limit, tax_rate in tax_bands:
            if remaining_taxable_income > 0:
                taxable_in_band = min(remaining_taxable_income, upper_limit - (tax_bands[tax_bands.index((upper_limit, tax_rate)) - 1][0] if tax_bands.index((upper_limit, tax_rate)) > 0 else 0))
                tax_due += taxable_in_band * tax_rate
                remaining_taxable_income -= taxable_in_band

        return tax_due