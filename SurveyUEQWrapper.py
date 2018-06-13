# coding=utf-8
from pprint import pprint

import pandas as pd
from pandas import json

import functions_files
from MysqlND import MysqlND
import operator

__author__ = 'alicia'


class SurveyUEQWrapper(object):
    """

    """
    def __init__(self):
        self.survey_data = []
        self.extract_responses_from_tfm_db()
        pprint(self.survey_data)
        self.write_results_in_excel()

    def extract_responses_from_tfm_db(self):
        """
                Wrapper adhoc - TFM suggestions - database -> tfm_mp_data
                Extract suggestions from database and export to excel
        """
        query = "SELECT data FROM encuestas"
        results = MysqlND.execute_query(query, ())

        self.survey_data = []
        for result in results:
            data = result[0]
            data = json.loads(data)
            response_values = {}
            # print(data)
            count_uxs = 0
            for key, value in data.iteritems():
                if 'ux_' in key:
                    count_uxs += 1
                    number_survey = int(key.replace("ux_", ""))
                    response_values[number_survey] = int(value)

            # response_values = sorted(response_values.items())
            print("Total = " + str(count_uxs))
            response_values_keys = response_values.keys()
            response_values_keys.sort()

            final_response_values = []
            count = 1
            # for key in response_values_keys:
            for key in range(1, 27):
                # print "%s: %s" % (key, response_values[key])
                if key in response_values_keys:
                # if count == key:
                    final_response_values.append(response_values[key])
                else:
                    final_response_values.append(3)
                    count += 1
                count += 1

            self.survey_data.append(final_response_values)

    def write_results_in_excel(self, file="UEQ_Data_Analysis_Tool_TFM_data.xlsx"):
        """

        :param file:
        """
        # Create a Pandas dataframe from the data.
        df = pd.DataFrame(self.survey_data)
        # Create a Pandas Excel writer using XlsxWriter as the engine.
        writer = pd.ExcelWriter(file, engine='xlsxwriter')
        # Convert the dataframe to an XlsxWriter Excel object.
        df.to_excel(writer, sheet_name='Hoja1', header=False)
        # Close the Pandas Excel writer and output the Excel file.
        writer.save()
