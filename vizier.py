#from google.cloud.aiplatform.vizier import Study, pyvizier
from simulate import simulate_a_life
import datetime
import argparse

import json
import datetime
from google.cloud import aiplatform
import os



if __name__ == "__main__":

    num_trials = 66

    parser = argparse.ArgumentParser()
    #parser.add_argument("--bucket_name", required=True)
    parser.add_argument("--start_year", required=False, default=2024)
    parser.add_argument("--final_year", required=False, default=2074)
    parser.add_argument("--retirement_year", required=False, default=2054)
    
    parser.add_argument("--starting_cash", required=False, default=10000)
    
    parser.add_argument("--fixed_interest_capital", required=False, default=1000)
    parser.add_argument("--fixed_interest_rate", required=False, default=0.02)

    parser.add_argument("--NSI_capital", required=False, default=50000)
    parser.add_argument("--NSI_interest_rate", required=False, default=0.02)

    parser.add_argument("--pension_capital", required=False, default=100000)
    parser.add_argument("--pension_growth_rate", required=False, default=0.03)

    parser.add_argument("--ISA_capital", required=False, default=100000)
    parser.add_argument("--ISA_growth_rate", required=False, default=0.03)

    parser.add_argument("--GIA_capital", required=False, default=100000)
    parser.add_argument("--GIA_growth_rate", required=False, default=0.03)

    parser.add_argument("--CG_strategy", required=False, default="harvest")

    parser.add_argument("--buffer_multiplier", required=False, default=1.1)

    parser.add_argument("--utility_income_multiplier", required=False, default=0.5)
    parser.add_argument("--utility_investments_multiplier", required=False, default=0.1)
    parser.add_argument("--utility_pension_multiplier", required=False, default=0.03)
    parser.add_argument("--utility_cap", required=False, default=50000)

    args = parser.parse_args()

    
    REGION = "europe-west1"
    PROJECT_ID = os.environ.get('PROJECT_ID')

    STUDY_DISPLAY_NAME = '{}_study_{}'.format(PROJECT_ID.replace('-', ''), datetime.datetime.now().strftime('%Y%m%d_%H%M%S')) #@param {type: 'string'}
    ENDPOINT = REGION + '-aiplatform.googleapis.com'
    PARENT = 'projects/{}/locations/{}'.format(PROJECT_ID, REGION)

    
    
   
    param_utility_income_multiplier = {
    'parameter_id': 'utility_income_multiplier',
    'double_value_spec': {
        'min_value': 0.01,
        'max_value': 1.0
    }}

    param_utility_investments_multiplier = {
    'parameter_id': 'utility_investments_multiplier',
    'double_value_spec': {
        'min_value': 0.01,
        'max_value': 1.0
    }}

    param_utility_pension_multiplier = {
    'parameter_id': 'utility_pension_multiplier',
    'double_value_spec': {
        'min_value': 0.01,
        'max_value': 1.0
    }}

    param_utility_cap = {
    'parameter_id': 'utility_cap',
    'double_value_spec': {
        'min_value': 10000,
        'max_value': 100000
    }}



    metric_utility = {
        'metric_id': 'utility',
        'goal': 'MAXIMIZE'
    }

    study = {
        'display_name': STUDY_DISPLAY_NAME,
        'study_spec': {
        'algorithm': 'ALGORITHM_UNSPECIFIED',
        'parameters': [param_utility_income_multiplier, param_utility_investments_multiplier, param_utility_pension_multiplier, param_utility_cap],
        'metrics': [metric_utility],
        }
    }
    vizier_client = aiplatform.gapic.VizierServiceClient(client_options=dict(api_endpoint=ENDPOINT))
    
    study = vizier_client.create_study(parent=PARENT, study=study)
    STUDY_NAME = study.name


    for i in range(0, num_trials):

        suggest_response = vizier_client.suggest_trials({
        'parent': STUDY_NAME,
        'suggestion_count': 1,
        })


        dd = {x.parameter_id: x.value for x in suggest_response.result().trials[0].parameters}
        
        args.utility_income_multiplier = dd['utility_income_multiplier']
        args.utility_investments_multiplier = dd['utility_investments_multiplier']
        args.utility_pension_multiplier = dd['utility_pension_multiplier']
        args.utility_cap = dd['utility_cap']


        RESULT = simulate_a_life(args)
        
        # vizier_client.add_trial_measurement({
        #     'trial_name': suggest_response.result().trials[0].name,
        #     'measurement': {
        #         'metrics': [{'metric_id': 'utility', 'value':RESULT }]
        #     }
        # })

        vizier_client.complete_trial({
        'name': suggest_response.result().trials[0].name,
        'final_measurement': {
                'metrics': [{'metric_id': 'utility', 'value':RESULT }]
        }
        })