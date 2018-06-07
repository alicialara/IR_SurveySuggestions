# coding: utf-8
__author__ = 'alicia'

import sys

import pandas as pd

import functions_files

reload(sys)
sys.setdefaultencoding('utf8')


class Document(object):
    def __init__(self, file_data, sheet_name):
        self.file_data = file_data
        self.sheet_name = sheet_name
        self.dir_output_name = file_data + '_output'
        self.pickle_file_data = file_data + ".pickle"
        self.pickle_file_data_text_complete = file_data + "_text.pickle"
        self.data = {}
        self.text_complete = {}
        self.get_document()

    def get_document(self):
        if functions_files.exists_pickle(self.pickle_file_data_text_complete):
            self.data = functions_files.get_pickle(self.pickle_file_data)
            self.text_complete = functions_files.get_pickle(self.pickle_file_data_text_complete)
        else:
            df = pd.read_excel(self.file_data + '.xlsx', sheetname=self.sheet_name, header=None)
            data = {}

            text_complete = ''
            for i in df.get_values():
                id = i[0]
                answer = i[1]
                # query = "INSERT INTO surveys_suggestions(id_question,suggestion) VALUES(%s,%s)"
                # MysqlND.execute_query(query, (id, answer,))
                data[id] = answer
                text_complete = text_complete + " " + answer

            self.data = data
            self.text_complete[0] = text_complete
            functions_files.save_pickle(self.pickle_file_data, self.data)
            functions_files.save_pickle(self.pickle_file_data_text_complete, self.text_complete)

    def get_data(self):
        return self.data

    def get_text_complete(self):
        return self.text_complete
