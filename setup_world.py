def generate_living_costs():
    d1 = {year: 30000*(1.02)**idx  for idx, year in enumerate(range(2024, 2054))}
    d2 = {year: d1[2053]*(1.04)**idx  for idx, year in enumerate(range(2054, 2074))}
    return {**d1, **d2}



def generate_salary():
    return {year: 150000*(.99)**idx  for idx, year in enumerate(range(2024, 2054))}



def linear_pension_draw_down_function(pot_value, current_year, retirement_year, final_year):
    if current_year == retirement_year:
        return 0.25*pot_value
    elif current_year < retirement_year:
        return 0
    else:
        years_left = final_year - current_year
        return pot_value/years_left

    
    