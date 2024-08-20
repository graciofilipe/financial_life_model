def generate_living_costs():
    d1 = {year: 40000*(1.02)**idx  for idx, year in enumerate(range(2024, 2054))}
    d2 = {year: d1[2053]*(1.04)**idx  for idx, year in enumerate(range(2054, 2074))}
    return {**d1, **d2}


def generate_salary():
    return {year: 150000*(1.005)**idx  for idx, year in enumerate(range(2024, 2054))}

def pension_draw_down_schedule(pension_total_pot, year_0, final_year, draw_down_rate):
    d0 ={year_0: pension_total_pot*0.25}
    d1 = {year: pension_total_pot*0.75/((1+draw_down_rate)**idx) for idx, year in enumerate(range(2054, 2074))}