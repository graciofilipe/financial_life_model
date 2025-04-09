def generate_living_costs():
    r1 = 1.02 # rate of increase until retirement
    r2 = 1.04 # rate of increase after retirement

    d1 = {year: 20000*(r1)**idx  for idx, year in enumerate(range(2025, 2055))}
    d2 = {year: d1[2054]*(r2)**idx  for idx, year in enumerate(range(2054, 2075))}
    return {**d1, **d2}



def generate_salary():
    r = 1.01 # salary growth rate 

    return {year: 100000*(r)**idx  for idx, year in enumerate(range(2024, 2054))}


# linear draw down minimizes expected income tax 
def linear_pension_draw_down_function(pot_value, current_year, retirement_year, final_year):
    
    # lump sum at retirement
    if current_year == retirement_year:
        return min(0.25*pot_value, 260000)
    
    elif current_year < retirement_year:
        return 0
    
    #linear draw down
    else:
        years_left = final_year - current_year
        return pot_value/years_left

    
    