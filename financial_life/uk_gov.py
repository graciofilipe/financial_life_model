class TaxMan:
    """
    Encapsulates UK government tax rules, including income tax, national insurance,
    capital gains tax, and pension allowances.
    """
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
        self.capital_gains_tax_rate = 0.24


    def capital_gains_tax_due(self, capital_gains, total_taxable_income=0):
        """
        Calculates the Capital Gains Tax due on investment gains.
        
        Args:
            capital_gains (float): The total capital gains realized.
            total_taxable_income (float): The individual's total taxable income (used to determine rate).

        Returns:
            float: The amount of tax due.
        """
        taxable_gains = max(0, capital_gains - self.capital_gains_tax_allowance)
        
        if taxable_gains <= 0:
            return 0
            
        tax_band = self.calculate_tax_band(total_taxable_income)
        
        if tax_band == "basic rate":
            # Check how much unused basic rate band is available
            # Basic rate band width is self.tax_bands[0] (37700)
            # Taxable income (Post-PA) = total_taxable_income - PA (roughly)
            # Ideally we use the exact unused band logic, but for now we use the rate based on the starting band.
            # Strictly speaking, gains can push you into the higher band.
            # Let's implement the "push" logic.
            
            personal_allowance = self.personal_allowance
            if total_taxable_income > self.personal_allowance_limit:
                reduction = (total_taxable_income - self.personal_allowance_limit) / 2
                personal_allowance = max(0, self.personal_allowance - reduction)
                
            taxable_income_amount = max(0, total_taxable_income - personal_allowance)
            unused_basic_band = max(0, self.tax_bands[0] - taxable_income_amount)
            
            amount_at_basic = min(taxable_gains, unused_basic_band)
            amount_at_higher = taxable_gains - amount_at_basic
            
            return (amount_at_basic * 0.18) + (amount_at_higher * 0.24)
            
        else:
            # Higher or Additional rate taxpayers pay 24% on all gains
            return taxable_gains * 0.24



    def calculate_tax_band(self, gross_income):
        """
        Determines the highest tax band applicable to the given Gross Income.

        Args:
            gross_income (float): The total gross income (before Personal Allowance).

        Returns:
            str: The tax band ("basic rate", "higher rate", or "additional rate").
        """
        # Calculate Personal Allowance for this income level
        personal_allowance = self.personal_allowance
        if gross_income > self.personal_allowance_limit:
            reduction = (gross_income - self.personal_allowance_limit) / 2
            personal_allowance = max(0, self.personal_allowance - reduction)

        taxable_income = max(0, gross_income - personal_allowance)

        if taxable_income <= self.tax_bands[0]:
            return "basic rate"
        elif gross_income >= self.tax_bands[1]: 
            # tax_bands[1] is 125140 (Gross threshold for Additional Rate)
            return "additional rate"
        else:
            return "higher rate"

    def calculate_interest_allowance(self, taxable_income):
        """
        Calculates the Personal Savings Allowance based on the tax band.

        Args:
            taxable_income (float): The total taxable income used to determine the tax band.

        Returns:
            int: The interest allowance amount (1000, 500, or 0).
        """
        tax_band = self.calculate_tax_band(taxable_income)
        if tax_band == "basic rate":
            return self.basic_rate_interest_allowance
        elif tax_band == "higher rate":
            return self.higher_rate_interest_allowance
        else:
            return self.additional_rate_interest_allowance

    def taxable_interest(self, taxable_income, gross_interest):
        """
        Calculates the amount of interest income that is subject to tax.

        Args:
            taxable_income (float): The total taxable income (used to determine allowance).
            gross_interest (float): The total gross interest earned.

        Returns:
            float: The taxable portion of the interest.
        """
        interest_allowance = self.calculate_interest_allowance(taxable_income=taxable_income)
        return max(0, gross_interest - interest_allowance)


    def pension_allowance(self, taxable_income_post_pension, individual_pension_contribution, employer_contribution):
        """
        Calculates the annual pension allowance, applying tapering rules for high earners.

        Args:
            taxable_income_post_pension (float): Taxable income after pension contributions.
            individual_pension_contribution (float): The individual's pension contribution.
            employer_contribution (float): The employer's pension contribution.

        Returns:
            float: The calculated pension allowance for the year.
        """
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

        # Annual NI thresholds and rates (2025/26)
        lower_threshold = 12570 # Primary Threshold
        upper_threshold = 50270 # Upper Earnings Limit
        lower_rate = 0.08 # Main rate
        upper_rate = 0.02 # Additional rate

        if annual_pay <= lower_threshold:
            return 0
        elif annual_pay <= upper_threshold:
            annual_contribution = (annual_pay - lower_threshold) * lower_rate
        else:
            annual_contribution = (upper_threshold - lower_threshold) * lower_rate + (annual_pay - upper_threshold) * upper_rate

        return annual_contribution