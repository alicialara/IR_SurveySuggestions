# coding: utf-8
__author__ = 'alicia'

from Document import Document
from SimpleTextRank import SimpleTextRank

# from KeywordExtraction import KeywordExtraction

print("Starting...")

language = 'S'
dir_with_data = 'file_name'
window = 4

document = Document(dir_with_data, 'Hoja1')
# data_suggestions = document.get_data()

document.file_data = dir_with_data + "_text_complete"
text_complete_suggestions = document.get_text_complete()

# str = SimpleTextRank(window, dir_with_data, data_suggestions)

str = SimpleTextRank(window, document.file_data, text_complete_suggestions)
