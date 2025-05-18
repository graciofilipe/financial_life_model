
class TaxMan:
    PENSION_THRESHOLD_INCOME_LIMIT = 200000
    PENSION_STANDARD_ANNUAL_ALLOWANCE = 60000
    PENSION_MINIMUM_TAPERED_ALLOWANCE = 10000
    PENSION_ADJUSTED_INCOME_TAPER_THRESHOLD = 260000
    ISA_ANNUAL_ALLOWANCE = 20000

    # UNIT TESTING: Each calculation method needs thorough testing with various inputs.
    # - calculate_uk_income_tax: Different bands, thresholds, zero income, personal allowance tapering.
    # - calculate_uk_national_insurance: Below LEL, between LEL/UEL, above UEL.
    # - capital_gains_tax_due: Gains below, at, and above allowance.
    # - pension_allowance: Complex; test various incomes (thresholds, tapering) and contributions.
    # - taxable_interest: Different income levels (for PSA) and interest amounts.
    def __init__(self):
        self.tax_bands = [37700, 125140]
        self.basic_rate = 0.2
        self.higher_rate = 0.40
        self.additional_rate = 0.45
        self.personal_allowance = 12570
        self.personal_allowance_limit = 100000
        self.basic_rate_interest_allowance = 1000
        self.higher_rate_interest_allowance = 500
        self.additional_rate_interest_allowance = 0
        self.capital_gains_tax_allowance = 3000
        self.capital_gains_tax_rate = 0.2


    def capital_gains_tax_due(self, capital_gains):
        taxable_gains = max(0, capital_gains - self.capital_gains_tax_allowance)
        return taxable_gains * self.capital_gains_tax_rate



    def calculate_tax_band(self, taxable_income):
        if taxable_income <= self.tax_bands[0]:
            return "basic rate"
        elif taxable_income >= self.tax_bands[1]:
            return "additional rate"
        else:
            return "higher rate"

    def calculate_interest_allowance(self, taxable_income):
        tax_band = self.calculate_tax_band(taxable_income)
        if tax_band == "basic rate":
            return self.basic_rate_interest_allowance
        elif tax_band == "higher rate":
            return self.higher_rate_interest_allowance
        else:
            return self.additional_rate_interest_allowance

    def taxable_interest(self, taxable_income, gross_interest):
        interest_allowance = self.calculate_interest_allowance(taxable_income=taxable_income)
        return max(0, gross_interest - interest_allowance)


    def pension_allowance(self, taxable_income_post_pension, individual_pension_contribution, employer_contribution):
        threshold_income = taxable_income_post_pension + individual_pension_contribution
        adjusted_income = taxable_income_post_pension + individual_pension_contribution + employer_contribution
        
        #tapered_allowance 
        if threshold_income < self.PENSION_THRESHOLD_INCOME_LIMIT:
            tapered_allowance = self.PENSION_STANDARD_ANNUAL_ALLOWANCE
        else:
            tapered_allowance = min(max(self.PENSION_MINIMUM_TAPERED_ALLOWANCE, self.PENSION_STANDARD_ANNUAL_ALLOWANCE - (adjusted_income - self.PENSION_ADJUSTED_INCOME_TAPER_THRESHOLD)/2), self.PENSION_STANDARD_ANNUAL_ALLOWANCE)

        return tapered_allowance



    def calculate_uk_income_tax(self, gross_income):
        """
        Calculates the amount of UK income tax due based on the provided gross income.

        Args:
            gross_income (float): The individual's total income before any deductions.

        Returns:
            float: The amount of income tax due.
        """

        personal_allowance = self.personal_allowance
        # Check if Personal Allowance is reduced due to high income
        if gross_income > self.personal_allowance_limit:
            personal_allowance_reduction = (gross_income - self.personal_allowance_limit) / 2
            personal_allowance = max(0, self.personal_allowance - personal_allowance_reduction)

        # Taxable income
        taxable_income = max(0, gross_income - personal_allowance)

        ## Calculate tax due
        tax_due = 0
        remaining_taxable_income = taxable_income
        
        # basic rate
        taxable_at_basic = max(0, min(taxable_income, self.tax_bands[0]))
        basic_tax = taxable_at_basic * self.basic_rate
        tax_due += basic_tax
        remaining_taxable_income -= taxable_at_basic

        # higher rate
        taxable_at_higher = max(0 , min(self.tax_bands[1] - self.tax_bands[0], remaining_taxable_income))
        higher_tax = taxable_at_higher * self.higher_rate
        tax_due += higher_tax
        remaining_taxable_income -= taxable_at_higher

        # additional rate
        taxable_at_additional = max(0, remaining_taxable_income)
        additional_tax = taxable_at_additional * self.additional_rate
        tax_due += additional_tax

        return tax_due



    def calculate_uk_national_insurance(self, annual_pay):
        """
        Calculates the amount of UK National Insurance contributions due based on the provided annual pay.

        Args:
            annual_pay (float): The individual's annual earnings.

        Returns:
            float: The amount of National Insurance contributions due for the year.
        """

        # Annual NI thresholds and rates (approximating 2023/24)
        lower_threshold = 1048*12 # LEL: Point below which 0 NI is paid
        upper_threshold = 4189*12 # UEL: Point above which rate drops
        lower_rate = 0.08 # Rate between PT (approx LEL) and UEL (rate changed in Jan '24, using 8%)
        upper_rate = 0.02

        if annual_pay <= lower_threshold:
            return 0
        elif annual_pay <= upper_threshold:
            annual_contribution = (annual_pay - lower_threshold) * lower_rate
        else:
            annual_contribution = (upper_threshold - lower_threshold) * lower_rate + (annual_pay - upper_threshold) * upper_rate

        return annual_contribution