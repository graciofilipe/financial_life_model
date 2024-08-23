from google.cloud import aiplatform
from google.cloud.aiplatform.vizier import Study, pyvizier
from simulate import simulate_a_life
import datetime


if __name__ == "__main__":

    project_id = os.environ.get('PROJECT_ID')


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

    PROJECT_ID = project_id
    LOCATION = "us-central1"  # @param {type:"string"}



    # These will be automatically filled in.
    STUDY_DISPLAY_NAME = "{}_study_{}".format(
        PROJECT_ID.replace("-", ""), datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    )
    PARENT = "projects/{}/locations/{}".format(PROJECT_ID, LOCATION)

    print("LOCATION: {}".format(LOCATION))
    print("PARENT: {}".format(PARENT))

    # Parameter Configuration
    problem = pyvizier.StudyConfig()
    #problem.algorithm = pyvizier.Algorithm.RANDOM_SEARCH

    # Objective Metrics
    problem.metric_information.append(
        pyvizier.MetricInformation(name="total_util", goal=pyvizier.ObjectiveMetricGoal.MAXIMIZE)
    )

    # Defines the parameters configuration.
    root = problem.search_space.select_root()
    root.add_float_param("utility_income_multiplier", 0, 1.0, scale_type=pyvizier.ScaleType.LINEAR)

    aiplatform.init(project=PROJECT_ID, location=LOCATION)
    study = Study.create_or_load(display_name=STUDY_DISPLAY_NAME, problem=problem)

    STUDY_ID = study.name
    print("STUDY_ID: {}".format(STUDY_ID))

    def create_metrics(trial_id, utility_income_multiplier):
        print(("=========== Start Trial: [{}] =============").format(trial_id))
        measurement = pyvizier.Measurement()
        measurement.metrics["total_util"] = simulate_a_life(utility_income_multiplier)
        return measurement


    worker_id = "worker1"  # @param {type: 'string'}
    suggestion_count_per_request = 3  # @param {type: 'integer'}
    max_trial_id_to_stop = 4  # @param {type: 'integer'}

    print("worker_id: {}".format(worker_id))
    print("suggestion_count_per_request: {}".format(suggestion_count_per_request))
    print("max_trial_id_to_stop: {}".format(max_trial_id_to_stop))

    while len(study.trials()) < max_trial_id_to_stop:
        trials = study.suggest(count=suggestion_count_per_request, worker=worker_id)

        for suggested_trial in trials:
            measurement = CreateMetrics(
                suggested_trial.name,
                suggested_trial.parameters["utility_income_multiplier"].value
            )
            suggested_trial.add_measurement(measurement=measurement)
            suggested_trial.complete(measurement=measurement)

    optimal_trials = study.optimal_trials()
    print("optimal_trials: {}".format(optimal_trials))