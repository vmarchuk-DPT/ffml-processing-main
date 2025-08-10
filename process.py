import os

import statistics
import pandas as pd
import paths as paths
import features as features
import rb_models as models

import psycopg2

import json
import datetime
import logging
import csv
from dotenv import load_dotenv
from logger import get_logger
from st import make_st

load_dotenv()
logger = get_logger('process.process')
import watchtower

#import boto3

# Set up boto3 client (optional, use default session if preferred)
#boto3_client = boto3.client('logs', region_name='us-east-1')


# Set up basic configuration for logging
#logging.basicConfig(
#    level=logging.DEBUG,  # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
#    format='%(asctime)s - %(levelname)s - %(message)s',  # Format for the log messages
#)

# Create a logger instance
#logger = logging.getLogger()

# Create a CloudWatch log handler
# cloudwatch_handler = watchtower.CloudWatchLogHandler(
 #   boto3_client=boto3_client,
 #   log_group='/ffml-processing',  # The CloudWatch log group name
 #   stream_name='{strftime:%Y-%m-%d}'  # You can use something dynamic like '{strftime:%Y-%m-%d}'
#)
#formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
#cloudwatch_handler.setFormatter(formatter)
# Add the handler to the logger
#logger.addHandler(cloudwatch_handler)

def read_database(cur, survey_version):
    results = []
    cur.execute(
        f"""
        select * from results 
        where survey_version_id = {survey_version}
        """
    )
    for res in cur.fetchall():
        results.append(
            paths.Result(
                unique_id=res[1],
                participant=res[2],
                question_type=res[3],
                question_stimulus=res[4],
                response=res[5],
                features=json.loads(res[6]),
                qlabel=res[8]
            )
        )

    return results


def read_survey_combination(cur, survey_combination_schema):
    """
    Function to pull results across multiple surveys,
    with option to specify mobile or computer data for each survey

    param survey_combination_schema (dict)
            structure examples {'615': {'computer_only' True, 'mobile_only': False}}
    :param cur (object) - psycopg2 cursor object

    :return: results (list)
    """
    results = []
    logging.info(f'Pulling data from multiple surveys: {survey_combination_schema}')
    for survey_id in survey_combination_schema:
        computer_data = True
        mobile_data = True
        if survey_combination_schema[survey_id]['computer_only']:
            mobile_data = False
        if survey_combination_schema[survey_id]['mobile_only']:
            computer_data = False

        survey_results = read_database(cur, survey_id)
        if computer_data and mobile_data:
            results.extend(survey_results)

        else:
            mob_participants, comp_participants = get_mobile_participants(cur, survey_id)
            logging.info(f'{survey_id} - Computer Participants: {len(mob_participants)},'
                         f' Mobile Participants: {len(comp_participants)}')
            if computer_data:
                for result in survey_results:
                    if result.participant not in mob_participants:
                        results.append(result)

            elif mobile_data:
                for result in survey_results:
                    if result.participant not in comp_participants:
                        results.append(result)

    return results


def get_mobile_participants(cur, survey_version):
    mobile_participants = []
    computer_participants = []
    cur.execute(
        f"""
        select participant from results 
        where survey_version_id = {survey_version} and
        response = 'Phone/Tablet'
        """
    )
    for res in cur.fetchall():
        mobile_participants.append(res[0])

    cur.execute(
        f"""
        select participant from results 
        where survey_version_id = {survey_version} and
        response = 'Computer'
        """
    )
    for res in cur.fetchall():
        computer_participants.append(res[0])

    return mobile_participants, computer_participants


def get_question_key(cur, survey_version):
    cur.execute(
        f"""
        SELECT known_element_of_interest.short_code, 
        known_element_of_interest.category, 
        known_element_of_interest.qlabel, 
        known_element_of_interest.id, 
        known_element_of_interest.qtitle, 
        STRING_AGG(known_element_of_interest_option.title, '|') AS options
        FROM known_element_of_interest
        JOIN known_element_of_interest_option ON known_element_of_interest.id = known_element_of_interest_option.known_element_of_interest_id
        GROUP BY known_element_of_interest.id
        HAVING known_element_of_interest.survey_version_id = {survey_version}
        """
    )

    qkey = {}
    all = cur.fetchall()
    for row in all: #cur.fetchall():
        row = list(row)
        qkey[row[2]] = list(row)
    return qkey


def update_analysis(conn, cur, people, survey_version, question_key, filepath):
    logging.info('Beginning processed_results upload')
    import pandas as pd
    provile_df_list = []
    for person in people:
        profile_df = pd.DataFrame(people[person].profile)
        profile_df = profile_df.reset_index()
        profile_df = pd.concat([profile_df['index'], profile_df['all'].apply(pd.Series)], axis=1)
        profile_df.columns = ['qlabel', 'response', 'certainty']
        profile_df['participant'] = person
        profile_df['suvey_version_id'] = survey_version
        provile_df_list.append(profile_df)


        #result_df = pd.DataFrame(people[person].results)
    df_union = pd.concat(provile_df_list, ignore_index=True)
    print(df_union)
    question_key_df = pd.DataFrame(question_key)
    print(question_key_df)
    df_union['question_stimulus'] = df_union['qlabel'].apply(lambda q: question_key_df[q].iloc[4] if q in question_key_df.columns else None)
    print(df_union)
    r = df_union.to_csv(f'df_result{survey_version}.csv')
    print(r)
    if True:
        print('bye!')
        return 'asd'


    if filepath:
        f = open(filepath, "wt")
        f = csv.writer(f)
        f.writerow(["survey_version_id", "survey_session_chunk_id", "participant",
                    "question_type", "question_stimulus", "response", "certainty"])
    null_count = 0
    non_null_count = 0
    for person in people:
        profile = people[person].profile
        results = people[person].results
        for key in results:  # survey session chunk
            result = results[key]
            ques = result.question_stimulus
            for row in question_key:
                if question_key[row][4] == ques:
                    break

            # Note -> probably a case of issues arising where there are no replies, due to dynamic survey questions.
            # Question -> does this affect other aspects of the processing?
            #if (question_key[row][1] in profile) and (question_key[row][0] in profile[question_key[row][1]]):

                try:
                    cert = profile[question_key[row][1]][question_key[row][0]].get("certainty")
                except Exception as err:
                    continue
                print('opa')
                print(f'cert = {cert}')
                result.question_stimulus = result.question_stimulus.replace("'", "''")
                result.response = result.response.replace("'", "''")
                if cert is not None:
                    if filepath:
                        f.writerow([survey_version, result.unique_id, person, result.question_type, result.question_stimulus, result.response, cert])
                    else:
                        try:
                            cur.execute(
                            f"""INSERT INTO processed_results
                            (survey_version_id, survey_session_chunk_id, participant, question_type, question_stimulus, response, certainty, qlabel)
                            VALUES
                            ({survey_version}, {result.unique_id}, '{person}', '{result.question_type}', '{result.question_stimulus}', '{result.response}', {cert}, '{result.qlabel}') 

                            """
                            )
                        except Exception as err:
                            print(f'error = {err}')
                            print(
                                f"""INSERT INTO processed_results
                                                        (survey_version_id, survey_session_chunk_id, participant, question_type, question_stimulus, response, certainty, qlabel)
                                                        VALUES
                                                        ({survey_version}, {result.unique_id}, '{person}', '{result.question_type}', '{result.question_stimulus}', '{result.response}', {cert}, '{result.qlabel}') 

                                                        """
                            )
                            conn.rollback()

                            continue
                        #ON
                        #CONFLICT(survey_session_chunk_id)
                        #DO
                        #UPDATE
                        #SET
                        #certainty = EXCLUDED.certainty
                    non_null_count += 1
                else:
                    cur.execute(
                        f"""INSERT INTO processed_results
                        (survey_version_id, survey_session_chunk_id, participant, question_type, question_stimulus, response, qlabel)
                        VALUES
                        ({survey_version}, {result.unique_id}, '{person}', '{result.question_type}', '{result.question_stimulus}', '{result.response}', '{result.qlabel}') 
                        """
                    )
                    #ON
                    #CONFLICT(survey_session_chunk_id)
                    #DO
                    #NOTHING
                    if result.question_type in ["bipartite_choice", "tripartite_choice"]:
                        logging.debug(f'Null cert: {result.unique_id}, {person}')
                        null_count += 1
            conn.commit()

    if not filepath:
        try:
            logging.info("Committing results")
            cur.execute(
                f"""
                INSERT INTO processed (survey_version_id, last_processed)
                VALUES
                ({survey_version}, '{datetime.datetime.now()}')
                ON CONFLICT (survey_version_id)
                DO UPDATE
                SET last_processed = EXCLUDED.last_processed 
                """
            )
            conn.commit()

        except Exception as e:
            logging.error(f"Error in commit to DB: {e}", exc_info=True)

        except psycopg2.error as e:
            logging.error(f"Error in commit to DB: {e}", exc_info=True)

    logging.info(f"Upload completed. Non-null results: {non_null_count}, Null results {null_count}")



def process(survey_version, surveys_join_schema=None):
    logger.info(f"Processing started for survey: {survey_version}")

    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST"),
        dbname="decipher",
        user=os.environ.get("POSTGRES_USERNAME"),
        password=os.environ.get("POSTGRES_PASSWORD"),
    )
    #make_st(conn)


    # Obtain a cursor for querying.
    cur = conn.cursor()

    people: dict[str, paths.Person] = {}

    fs = features.FeatureStats()
    model = models.Model()

    # If using specified schema for joining surveys, read this
    # Otherwise pull all data from specified survey verison
    if surveys_join_schema:
        results = read_survey_combination(cur, surveys_join_schema)
    else:
        results = read_database(cur, survey_version)

    logger.info(f"Database read complete, {len(results)} results found")
    question_key = get_question_key(cur, survey_version)

    for result in results:
        if result.participant not in people:
            people[result.participant] = paths.Person(result.participant, question_key)

        people[result.participant].add_result(result)
        fs.add_result(result)

    logger.info(f"People unpacked, {len(people)} participants found")

    del_people = []
    cert_people = {}
    people_normalised = 0
    results_normalised = 0
    error_enr = 0
    certs = []
    fs.prepare_stats()

    for person in people:
        for result in people[person].results:
            if people[person].results[result].question_type not in [
                "bipartite_choice",
                "tripartite_choice",
            ]:
                continue
            try:
                fs.normalize(people[person].results[result])
                if person not in cert_people:
                    cert_people[person] = []

                cert_people[person].append(
                    [
                        people[person].results[result].qlabel,
                        model.certainty(people[person].results[result]),
                    ]
                )

                certs.append(cert_people[person][-1][1])
                results_normalised += 1

            except ValueError as e:
                logging.error(f"Error in enrichment: {e}", exc_info=True)
                logging.debug(vars(people[person].results[result]))
                logging.debug(f"ValueError on {person}, {e}, {person}, "
                              f"{people[person].results[result].qlabel}")
                error_enr += 1
                # del_people.append(person)

        people_normalised += 1
        if people_normalised % 100 == 0:
            logging.info(f"Persons Processed {people_normalised},"
                         f" Results Normalised: {results_normalised},"
                         f" Normalisation Errors: {error_enr}")

    logging.info(f"Persons Processed {people_normalised},"
                 f" Results Normalised: {results_normalised},"
                 f" Normalisation Errors: {error_enr}")

    # Calculate necessary stats for certainty.
    avg = statistics.mean(certs)

    sdev = statistics.stdev(certs) if len(certs) >1 else 0.0
    cert_floor = avg - (2 * sdev)
    cert_ceil = avg + (2 * sdev)
    deciles = (cert_ceil - cert_floor) / 10

    # Figure out which decile we are in between 2sd below and 2sd above mean.
    for person in cert_people:
        for res in cert_people[person]:
            if res[1] > cert_ceil:
                res[1] = cert_ceil
            if res[1] < cert_floor:
                res[1] = cert_floor
            tracker = cert_floor
            dec = 0
            while res[1] > tracker:
                dec += 1
                tracker += deciles
            people[person].add_certainty(res[0], dec / 10)

    # Delete broken profiles from analysis.
    for person in del_people:
        logger.info(f"{len(del_people)} broken persons detected")
        del people[person]

    # Add an extra field to each bipartite/tripartite question
    # indicating the relative uncertainty viz benchmarks
    error_enr = 0
    for person in people:
        try:
            if "benchmark" not in people[person].profile:
                continue
            conf = []
            for var in people[person].profile["benchmark"]:
                if "certainty" in people[person].profile["benchmark"][var]:
                    conf.append(people[person].profile["benchmark"][var]["certainty"])

            if not conf:
                continue
            benchmark = statistics.mean(conf)
            # Normalize the paths
            for result in people[person].results:
                if people[person].results[result].question_type not in [
                    "bipartite_choice",
                    "tripartite_choice",
                ]:
                    continue
                people[person].add_relative(
                    benchmark, people[person].results[result].qlabel
                )

        except ValueError as e:
            logging.error(f"Error in relative certainty: {e}", exc_info=True)
            logging.debug(f"ValueError on {person}, {e}, {person}, "
                          f"{people[person].results[result].qlabel}")
            error_enr += 1

    logging.info(f'Relative Certainty Errors: {error_enr}')

    update_analysis(conn, cur, people, survey_version, question_key, None)
    print("Analysis Processing Completed")

    cur.close()
    conn.close()

    return people
