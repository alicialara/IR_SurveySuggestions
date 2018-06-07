# coding: utf-8
__author__ = 'alicia'

import pandas as pd
from MysqlND import MysqlND
import functions_files
import json

class Document(object):
    def __init__(self, file_data, sheet_name):
        self.file_data = file_data
        self.sheet_name = sheet_name
        self.dir_output_name = file_data + '_output'
        self.pickle_file_data = file_data + ".pickle"
        self.pickle_file_data_text_complete = file_data + "_text.pickle"
        self.data = {}
        self.text_complete = {}

        if self.file_data == 'db_tfm_mp_data' and not functions_files.exists_file(self.file_data + '.xlsx'):
            self.extract_suggestions_from_tfm_db()

        self.get_document()

    def get_document(self):
        if functions_files.exists_pickle(self.pickle_file_data_text_complete):
            self.data = functions_files.get_pickle(self.pickle_file_data)
            self.text_complete = functions_files.get_pickle(self.pickle_file_data_text_complete)
        else:
            if functions_files.exists_file(self.file_data + '.xlsx'):
                df = pd.read_excel(self.file_data + '.xlsx', sheetname=self.sheet_name, header=None)
                data = {}

                text_complete = ''
                for i in df.get_values():
                    id = i[0]
                    answer = i[1]
                    query = "SELECT suggestion FROM surveys_suggestions WHERE id_question=%s AND file=%s AND suggestion=%s"
                    results = MysqlND.execute_query(query, (id, self.file_data, answer,))
                    if results.rowcount == 0:
                        query = "INSERT INTO surveys_suggestions(id_question,suggestion,file) VALUES(%s,%s,%s)"
                        MysqlND.execute_query(query, (id, answer, self.file_data,))
                    data[id] = answer
                    text_complete = text_complete + " " + answer

                self.data = data
                self.text_complete['-1'] = text_complete
                functions_files.save_pickle(self.pickle_file_data, self.data)
                functions_files.save_pickle(self.pickle_file_data_text_complete, self.text_complete)
            else:
                raise Exception("The Excel file does not exist!!")


    def get_data(self):
        return self.data

    def get_text_complete(self):
        return self.text_complete

    def extract_suggestions_from_tfm_db(self):
        """
                Wrapper adhoc - TFM suggestions - database -> tfm_mp_data
                Extract suggestions from database and export to excel
        """
        query = "SELECT data FROM encuestas"
        results = MysqlND.execute_query(query, ())
        oa_1 = []
        oa_2 = []
        oa_3 = []
        for result in results:
            data = result[0]
            data = json.loads(data)
            if len(data['oa_1'])>1:
                oa_1.append(functions_files.strip_tags(data['oa_1']))
            if len(data['oa_2']) > 1:
                oa_2.append(functions_files.strip_tags(data['oa_2']))
            if len(data['oa_3']) > 1:
                oa_3.append(functions_files.strip_tags(data['oa_3']))


        # Create a Pandas dataframe from the data.
        df = pd.DataFrame(oa_1)
        # Create a Pandas Excel writer using XlsxWriter as the engine.
        writer = pd.ExcelWriter('oa1.xlsx', engine='xlsxwriter')
        # Convert the dataframe to an XlsxWriter Excel object.
        df.to_excel(writer, sheet_name='Hoja1', header=False)
        # Close the Pandas Excel writer and output the Excel file.
        writer.save()

        # Create a Pandas dataframe from the data.
        df = pd.DataFrame(oa_2)
        # Create a Pandas Excel writer using XlsxWriter as the engine.
        writer = pd.ExcelWriter('oa2.xlsx', engine='xlsxwriter')
        # Convert the dataframe to an XlsxWriter Excel object.
        df.to_excel(writer, sheet_name='Hoja1', header=False)
        # Close the Pandas Excel writer and output the Excel file.
        writer.save()

        # Create a Pandas dataframe from the data.
        df = pd.DataFrame(oa_3)
        # Create a Pandas Excel writer using XlsxWriter as the engine.
        writer = pd.ExcelWriter('oa3.xlsx', engine='xlsxwriter')
        # Convert the dataframe to an XlsxWriter Excel object.
        df.to_excel(writer, sheet_name='Hoja1', header=False)
        # Close the Pandas Excel writer and output the Excel file.
        writer.save()

