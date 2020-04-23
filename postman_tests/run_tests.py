from __future__ import absolute_import
from subprocess import Popen
import os
import json
import sys
from lib import newman
from lib import datastore


postman_tests_directory = os.path.dirname(os.path.abspath(__file__))
newman_data_path = os.path.join(postman_tests_directory, 'data', 'newman_data.json')
config_path = os.path.join(postman_tests_directory, 'config')


def create_reports_directory_if_not_exists(report_path):
    """ Creates the directory where the report generated by newman command is stored

    Args:
        report_path: string

    Returns:
        None
    """
    if not os.path.exists(report_path):
        os.makedirs(report_path)


def get_newman_command():
    """ Returns the newman shell command to be used for running the tests

    Args:
        None

    Returns:
        (str): The shell command to be used for running the tests
    """
    collection_data_path = os.path.join(postman_tests_directory, 'data', 'ner_collection.json')
    if os.path.exists(f"{config_path}/dev.json"):
        report_path = os.path.join(postman_tests_directory, 'newman_reports')
        create_reports_directory_if_not_exists(report_path)
        environment_file_path = f'{config_path}/dev.json'
        return (
            f'newman run {collection_data_path} -d {newman_data_path}'
            f' -e {environment_file_path} -r cli,htmlextra --reporter-htmlextra-logs'
            f' --reporter-htmlextra-export {report_path}'
        )
    else:
        environment_file_path = f'{config_path}/prod.json'
        return (
            f'newman run {collection_data_path} -d {newman_data_path}'
            f' -e {environment_file_path}'
        )


def run_tests():
    """ Runs the newman test-suite

    Args:
        None

    Returns:
        (int): The return code of the newman command
    """
    entities_data_path = os.path.join(postman_tests_directory, 'data', 'entities')
    datastore_data_path = os.path.join(postman_tests_directory, 'data', 'data_store')
    try:
        newman.check_if_data_valid(entities_data_path)
        datastore.sync(datastore_data_path, config_path, 'create')
        newman_data = newman.generate_newman_data(entities_data_path)
        with open(newman_data_path, 'w') as fp:
            json.dump(newman_data, fp)
        newman_command = get_newman_command()
        process = Popen(newman_command, shell=True)
        process.communicate()
        os.remove(newman_data_path)
        return process.returncode
    except Exception as e:
        raise e
    finally:
        datastore.sync(datastore_data_path, config_path, 'delete')


if __name__ == "__main__":
    status = run_tests()
    sys.exit(status)
