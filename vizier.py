#from google.cloud.aiplatform.vizier import Study, pyvizier
from simulate import simulate_a_life
import datetime
import argparse

import json
import datetime
from google.cloud import aiplatform
import os
import plotly.express as px
from datetime import datetime
from google.cloud import storage




if __name__ == "__main__":


    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket_name", required=True)
    parser.add_argument("--num_trials", required=False, default=11)
    parser.add_argument("--plot_best", required=False, default=False)
    parser.add_argument("--file_name", required=False, default="sim")



    parser.add_argument("--start_year", required=False, default=2024)
    parser.add_argument("--final_year", required=False, default=2074)
    parser.add_argument("--retirement_year", required=False, default=2054)
    
    parser.add_argument("--starting_cash", required=False, default=55000)
    
    parser.add_argument("--fixed_interest_capital", required=False, default=1000)
    parser.add_argument("--fixed_interest_rate", required=False, default=0.02)

    parser.add_argument("--NSI_capital", required=False, default=50000)
    parser.add_argument("--NSI_interest_rate", required=False, default=0.02)

    parser.add_argument("--pension_capital", required=False, default=150000)
    parser.add_argument("--pension_growth_rate", required=False, default=0.02)

    parser.add_argument("--ISA_capital", required=False, default=200000)
    parser.add_argument("--ISA_growth_rate", required=False, default=0.02)

    parser.add_argument("--GIA_capital", required=False, default=700000)
    parser.add_argument("--GIA_growth_rate", required=False, default=0.02)

    parser.add_argument("--CG_strategy", required=False, default="harvest")

    parser.add_argument("--buffer_multiplier", required=False, default=1.2)

    parser.add_argument("--utility_income_multiplier_ret", required=False, default=0.5)
    parser.add_argument("--utility_investments_multiplier_ret", required=False, default=0.1)
    parser.add_argument("--utility_pension_multiplier_ret", required=False, default=0.03)
    
    parser.add_argument("--utility_income_multiplier_working", required=False, default=0.5)
    parser.add_argument("--utility_investments_multiplier_working", required=False, default=0.1)
    parser.add_argument("--utility_pension_multiplier_working", required=False, default=0.03)
    
    parser.add_argument("--utility_constant", required=False, default=5000)
    parser.add_argument("--utility_cap", required=False, default=150000)

    args = parser.parse_args()

    
    REGION = "europe-west1"
    PROJECT_ID = os.environ.get('PROJECT_ID')

    STUDY_DISPLAY_NAME = '{}_study_{}'.format(PROJECT_ID.replace('-', ''), datetime.now().strftime('%Y%m%d_%H%M%S')) #@param {type: 'string'}
    ENDPOINT = REGION + '-aiplatform.googleapis.com'
    PARENT = 'projects/{}/locations/{}'.format(PROJECT_ID, REGION)

    
    

    param_utility_income_multiplier_work = {
    'parameter_id': 'utility_income_multiplier_work',
    'double_value_spec': {
        'min_value': 0.01,
        'max_value': 1.2
    }}

    param_utility_investments_multiplier_work = {
    'parameter_id': 'utility_investments_multiplier_work',
    'double_value_spec': {
        'min_value': 0.01,
        'max_value': 1.2
    }}

    param_utility_pension_multiplier_work = {
    'parameter_id': 'utility_pension_multiplier_work',
    'double_value_spec': {
        'min_value': 0.01,
        'max_value': 1.2
    }}


    param_utility_income_multiplier_ret = {
    'parameter_id': 'utility_income_multiplier_ret',
    'double_value_spec': {
        'min_value': 0.01,
        'max_value': 2
    }}

    param_utility_investments_multiplier_ret = {
    'parameter_id': 'utility_investments_multiplier_ret',
    'double_value_spec': {
        'min_value': 0.01,
        'max_value': 2
    }}

    param_utility_pension_multiplier_ret = {
    'parameter_id': 'utility_pension_multiplier_ret',
    'double_value_spec': {
        'min_value': 0.01,
        'max_value': 2
    }}

    param_utility_base = {
    'parameter_id': 'utility_base',
    'double_value_spec': {
        'min_value': 100,
        'max_value': 10000
    }}
    param_utility_cap = {
    'parameter_id': 'utility_cap',
    'double_value_spec': {
        'min_value': 100000,
        'max_value': 1000000
    }}

    metric_utility = {
        'metric_id': 'utility',
        'goal': 'MAXIMIZE'
    }

    metric_utility_sd = {
        'metric_id': 'utility_sd',
        'goal': 'MINIMIZE'
    }

    study = {
        'display_name': STUDY_DISPLAY_NAME,
        'study_spec': {
        'algorithm': 'ALGORITHM_UNSPECIFIED',
        'parameters': [param_utility_income_multiplier_work, param_utility_investments_multiplier_work, param_utility_pension_multiplier_work,
                       param_utility_income_multiplier_ret, param_utility_investments_multiplier_ret, param_utility_pension_multiplier_ret,
                       param_utility_base, param_utility_cap],
        'metrics': [metric_utility, metric_utility_sd],
        }
    }
    vizier_client = aiplatform.gapic.VizierServiceClient(client_options=dict(api_endpoint=ENDPOINT))
    
    study = vizier_client.create_study(parent=PARENT, study=study)
    STUDY_NAME = study.name


    for i in range(0, int(args.num_trials)):

        suggest_response = vizier_client.suggest_trials({
        'parent': STUDY_NAME,
        'suggestion_count': 1,
        })


        dd = {x.parameter_id: x.value for x in suggest_response.result().trials[0].parameters}
        
        args.utility_income_multiplier_work = dd['utility_income_multiplier_work']
        args.utility_investments_multiplier_work = dd['utility_investments_multiplier_work']
        args.utility_pension_multiplier_work = dd['utility_pension_multiplier_work']

        args.utility_income_multiplier_ret = dd['utility_income_multiplier_ret']
        args.utility_investments_multiplier_ret = dd['utility_investments_multiplier_ret']
        args.utility_pension_multiplier_ret = dd['utility_pension_multiplier_ret']

        args.utility_cap = dd['utility_cap']
        args.utility_base = dd['utility_base']

        RESULT, df = simulate_a_life(args)
        
        vizier_client.complete_trial({
        'name': suggest_response.result().trials[0].name,
        'final_measurement': {
                'metrics': [{'metric_id': 'utility', 'value': RESULT }, 
                            {'metric_id': 'utility_sd', 'value': df['Utility'].std()/df['Utility'].mean()}]
        }
        })
    
    if args.plot_best:

        print('DOING BEST TRIAL')
        opt_trial = vizier_client.list_optimal_trials({'parent': STUDY_NAME})
        
        optimal_parameters = {x.parameter_id: x.value for x in opt_trial.optimal_trials[0].parameters}
        
        args.utility_income_multiplier_work = optimal_parameters['utility_income_multiplier_work']
        args.utility_investments_multiplier_work = optimal_parameters['utility_investments_multiplier_work']
        args.utility_pension_multiplier_work = optimal_parameters['utility_pension_multiplier_work']

        args.utility_income_multiplier_ret = optimal_parameters['utility_income_multiplier_ret']
        args.utility_investments_multiplier_ret = optimal_parameters['utility_investments_multiplier_ret']
        args.utility_pension_multiplier_ret = optimal_parameters['utility_pension_multiplier_ret']
        
        args.utility_cap = optimal_parameters['utility_cap']
        args.utility_bsae = optimal_parameters['utility_base']

        RESULT, df = simulate_a_life(args)

        fig = px.line(df, x=df.index, y=df.columns, title='Financial Simulation')
        fig.update_xaxes(title_text='Year')
        fig.update_yaxes(title_text='Value')
        
        # Write to GCS
        file_name = f'{args.file_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        storage_client = storage.Client()
        bucket = storage_client.bucket(args.bucket_name)
        blob = bucket.blob(file_name)
        fig.write_html(f"/tmp/{file_name}")
        blob.upload_from_filename(f"/tmp/{file_name}")
        print(f"HTML file uploaded to gs://{args.bucket_name}/{file_name}")