# coding: utf-8
__author__ = 'alicia'
import itertools
import operator
import re
import unicodedata

import matplotlib.pyplot as plt
import networkx as nx
from nltk.util import ngrams
from stanfordcorenlp import StanfordCoreNLP

import functions_files
from MysqlND import MysqlND


class SimpleTextRank(object):
    def __init__(self, window, file, data):
        """
        Clase para la extraccin de palabras clave. Devuelve un Count con las palabras obtenidas
        :param window: int - Valor de ventana (palabras que coge antes y despus)
        :param archivo: string - Archivo seleccionado. False para coger todos los archivos disponibles
        """
        self.dir_with_data = file
        self.data = data
        self.window = window
        self.language = 'es'
        # variables auxiliares
        self.ngrams_window = {0: 1, 1: 3, 2: 5, 3: 7, 4: 9, 5: 11}

        self.texts_not_tagged = {}
        self.texts_tagged = {}
        self.texts_filtered = {}

        # self.data = dict(list(islice(self.data.iteritems(), 2)))
        self.execute()

    def execute(self):
        # for id_suggestion, suggestion in self.data.iteritems():
        for id_suggestion, suggestion in self.data.items():
            text = self.elimina_tildes(suggestion)
            self.texts_not_tagged[id_suggestion] = text
            if id_suggestion != 0:
                query = "SELECT tags FROM surveys_suggestions WHERE id_question=%s "
                results = MysqlND.execute_query(query, (id_suggestion,))
                result = results.fetchone()
                if result[0] is None:
                    self.texts_tagged[id_suggestion] = self.calcula_tags(text)
                    update = "UPDATE surveys_suggestions SET tags=%s WHERE id_question=%s"
                    MysqlND.execute_query(update, (self.texts_tagged[id_suggestion], id_suggestion,))

                else:
                    self.texts_tagged[id_suggestion] = result[0]
            else:
                query = "SELECT tags FROM surveys_suggestions"
                results = MysqlND.execute_query(query, ())
                self.texts_tagged[id_suggestion] = ''
                for res in results:
                    self.texts_tagged[id_suggestion] = self.texts_tagged[id_suggestion] + ' ' + res[0]

        self.filter_tags_texts()

        self.keywords_extraction()

    def keywords_extraction(self):
        loop_tagged_attributes = {self.dir_with_data: self.texts_filtered}
        for name, item in loop_tagged_attributes.iteritems():
            name = str(name)
            functions_files.create_dir_if_not_exists(self.dir_with_data + '/' + name)
            functions_files.create_dir_if_not_exists(self.dir_with_data + '/' + name + '/keyphrases')
            functions_files.create_dir_if_not_exists(
                self.dir_with_data + '/' + name + '/keyphrases/ventana_' + str(self.window))
            functions_files.create_dir_if_not_exists(self.dir_with_data + '/' + name + '/calculated_textrank')
            functions_files.create_dir_if_not_exists(self.dir_with_data + '/' + name + '/grafos_sin_pesos')
            functions_files.create_dir_if_not_exists(self.dir_with_data + '/' + name + '/grafos_sin_pesos/capturas')
            functions_files.create_dir_if_not_exists(
                self.dir_with_data + '/' + name + '/grafos_sin_pesos/capturas/ventana_' + str(self.window))
            functions_files.create_dir_if_not_exists(
                self.dir_with_data + '/' + name + '/grafos_sin_pesos/ventana_' + str(self.window))
            functions_files.create_dir_if_not_exists(self.dir_with_data + '/' + name + '/grafos_con_pesos')
            functions_files.create_dir_if_not_exists(self.dir_with_data + '/' + name + '/grafos_con_pesos/capturas')
            functions_files.create_dir_if_not_exists(
                self.dir_with_data + '/' + name + '/grafos_con_pesos/capturas/ventana_' + str(self.window))
            functions_files.create_dir_if_not_exists(
                self.dir_with_data + '/' + name + '/grafos_con_pesos/ventana_' + str(self.window))

            for file_name, array_ in item.iteritems():
                words = []  # array con las palabras de cada archivo ya filtradas
                for word in array_:
                    words.append(word)
                words = [x.lower() for x in words]

                # word_set_list = list(grams_list)
                unique_word_set = self.unique_everseen(words)
                word_set_list = list(unique_word_set)
                # pprint(word_set_list[:10])

                graph = self.create_graph(words, word_set_list)

                calculated_page_rank = nx.pagerank(graph,
                                                   weight='weight')  # cálculo de textRank con pesos (los pesos están en graph)

                self.save_textrank_results(calculated_page_rank, name, file_name)

                keywords = sorted(calculated_page_rank, key=calculated_page_rank.get, reverse=True)
                keywords = keywords[0:((len(word_set_list) / 3) + 1)]
                # pprint(keywords)

                selected_keywords = self.select_keywords_windowed(words, keywords)
                # pprint(selected_keywords)

                # ya tengo las palabras clave, asi que ahora puedo construir al grafo teniendo en cuenta la ventana
                # recorro todas las palabras del texto (words), y resalto las que aparecen como palabras clave

                # Cuando acabe, creo el grafo con las palabras obtenidas que co-ocurren en el texto
                # sabiendo que cada union de palabras es una arista entre los vertices (palabras)
                file_name = str(file_name)
                file_name_ = file_name.replace(".txt", "")
                file_name_ = file_name_.replace(".txt.final", "")
                file_name_ = file_name_.replace(".txt.tagged", "")

                graph_windowed = self.create_graph_windowed(selected_keywords, False)

                self.paint_graph(graph_windowed,
                                 self.dir_with_data + '/' + name + '/grafos_sin_pesos/capturas/ventana_' + str(
                                     self.window) + '/' + file_name_ + '.png', False)
                nx.write_pajek(graph_windowed, self.dir_with_data + '/' + name + '/grafos_sin_pesos/ventana_' + str(
                    self.window) + '/' + file_name_ + '.net')

                functions_files.replace(self.dir_with_data + '/' + name + '/grafos_sin_pesos/ventana_' + str(
                    self.window) + '/' + file_name_ + '.net', '0.0 0.0 ellipse', '')

                graph_windowed = self.create_graph_windowed(selected_keywords, True)

                self.paint_graph(graph_windowed,
                                 self.dir_with_data + '/' + name + '/grafos_con_pesos/capturas/ventana_' + str(
                                     self.window) + '/' + file_name_ + '.png', False)
                nx.write_pajek(graph_windowed, self.dir_with_data + '/' + name + '/grafos_con_pesos/ventana_' + str(
                    self.window) + '/' + file_name_ + '.net')

                functions_files.replace(self.dir_with_data + '/' + name + '/grafos_con_pesos/ventana_' + str(
                    self.window) + '/' + file_name_ + '.net', '0.0 0.0 ellipse', '')

                self.save_keywords(selected_keywords, name, file_name_)

    def unique_everseen(self, iterable, key=None):
        """List unique elements, preserving order. Remember all elements ever seen."""
        # unique_everseen('AAAABBBCCDAABBB') --> A B C D
        # unique_everseen('ABBCcAD', str.lower) --> A B C D
        seen = set()
        seen_add = seen.add
        if key is None:
            for element in itertools.ifilterfalse(seen.__contains__, iterable):
                seen_add(element)
                yield element
        else:
            for element in key:
                k = key(element)
                if k not in seen:
                    seen_add(k)
                    yield element

    def create_graph(self, words, word_set_list):
        # creo un grafo como explica el paper, teniendo en cuenta el valor de ventana.
        # si divido words en n-gramas, siendo n la ventana, obtengo la lista de palabras que comparar. Por ejemplo:
        # si ventana = 2, words = [A, B, C, D, E, B, G] y keywords = [B, C, G]
        # obtengo los bigramas AB, BC, CD, DE, EB, BG.
        # De ahi selecciono los que existen en keywords y los anado: [BC, BG].
        # Para anadirlos, separo las palabras por un espacio: B + " " + G
        # * Si ventana = 3, hago primero ventana=2 y luego ventana=3
        print("Ngrams (window) selected: " + str(self.window))
        grams_ = ngrams(words, self.window)
        # grams_ = ngrams(words, 2)
        grams_ = list(grams_)
        graph = nx.Graph()
        array_valores = {}
        for i, val in enumerate(grams_):
            ant = 0
            for k in range(1, self.window):
                # print "Anado " + str(val[ant]) + " - " + str(val[k]) +
                # " con posiciones en : " + str(ant) + " - " + str(k)
                key = val[ant] + '/' + val[k]
                if key in array_valores:
                    array_valores[key] += 1
                else:
                    array_valores[key] = 1
                ant += 1
        # pprint(array_valores)
        for key, value in array_valores.items():
            clave = key.split("/")
            graph.add_edge(clave[0], clave[1], weight=value)

        return graph

    def select_keywords_windowed(self, words, keywords):
        # si divido words en n-gramas, siendo n la ventana, obtengo la lista de palabras que comparar. Por ejemplo:
        # si ventana = 2, words = [A, B, C, D, E, B, G] y keywords = [B, C, G]
        # obtengo los bigramas AB, BC, CD, DE, EB, BG.
        # De ahi selecciono los que existen en keywords y los anado: [BC, BG].
        # Para anadirlos, separo las palabras por un espacio: B + " " + G
        selected_keywords = []
        grams_ = ngrams(words, int(self.window))
        grams_ = list(grams_)
        for i, val in enumerate(grams_):
            keywords_aux = []
            aux = True
            for k in range(int(self.window)):
                keywords_aux.append(val[k])
                if val[k] not in keywords:
                    aux = False
            if aux:
                new_keyword = " ".join(keywords_aux)
                selected_keywords.append(new_keyword)

        return selected_keywords

    def create_graph_windowed(self, selected_keywords, conPesos):
        # creo un grafo como explica el paper (figura 2), teniendo en cuenta el valor de ventana.
        graph = nx.Graph()
        array_valores = {}
        for val in selected_keywords:
            keywords = val.split(" ")
            ant = 0
            for i in range(1, len(keywords)):
                key = keywords[ant] + '/' + keywords[i]
                if key in array_valores:
                    array_valores[key] += 1
                else:
                    array_valores[key] = 1
                ant += 1
        for key, value in array_valores.items():
            clave = key.split("/")
            graph.add_edge(clave[0], clave[1], weight=value)
        return graph

    def paint_graph(self, graph, name, weighted=True):
        print("graph %s has %d nodes with %d edges" % (graph.name, nx.number_of_nodes(graph), nx.number_of_edges(graph)))

        if weighted:
            elarge = [(u, v) for (u, v, d) in graph.edges(data=True) if d['weight'] > 2]
            esmall = [(u, v) for (u, v, d) in graph.edges(data=True) if d['weight'] <= 2]
        else:
            elarge = None
            esmall = None

        pos = nx.spring_layout(graph)  # positions for all nodes
        # nodes
        nx.draw_networkx_nodes(graph, pos, node_size=100)

        # edges
        nx.draw_networkx_edges(graph, pos, edgelist=elarge,
                               width=1)
        nx.draw_networkx_edges(graph, pos, edgelist=esmall,
                               width=1, alpha=1, edge_color='b', style='dashed')

        # labels
        nx.draw_networkx_labels(graph, pos, font_size=6, font_family='sans-serif')

        plt.axis('off')
        plt.savefig(name)  # save as png

    def save_keywords(self, keywords, name, file):

        file_write = self.dir_with_data + '/' + name + '/keyphrases/ventana_' + str(
            self.window) + '/' + file + '.txt.result'
        for word in keywords:
            with open(file_write, "a") as myfile:
                myfile.write(str(word) + "\n")

    def save_textrank_results(self, calculated_textrank, name, file):
        sorted_x = dict(sorted(calculated_textrank.items(), key=operator.itemgetter(1)))
        file_write = self.dir_with_data + '/' + str(name) + '/calculated_textrank/' + str(file) + '_' + str(self.window) + '.textrank'
        for word, value in sorted_x.iteritems():
            with open(file_write, "a") as myfile:
                myfile.write(str(word) + " -> " + str(value) + "\n")

    def filter_tags_texts(self):
        loop_tagged_attributes = {'texts_tagged': self.texts_tagged}
        for name, item in loop_tagged_attributes.iteritems():
            for file, text in item.iteritems():
                # tengo que convertirlo en array y filtrar los datos que me interesan (nombres y adjetivos)
                data = []
                miarray = text.split(" ")
                for palabra in miarray:
                    if palabra != '':
                        aux = palabra.split("/")
                        # print file + " " + palabra
                        if (aux[1] == 'NOUN') or (aux[1] == 'ADJ'):
                            # entonces es buena
                            # a partir de ahora no me sirve pos POS TAGS (porque ya estn filtradas)
                            palabra = palabra.replace("/NOUN", "").replace("/ADP", "").replace("/ADJ", "")
                            data.append(palabra)
                self.texts_filtered[file] = data

        return True

    def calcula_tags(self, text):

        # text = text.decode('utf-8')
        text = self.cleanhtml(text)
        # token = re.sub(r'\([^)]*\)', '', token)  # elimino paréntesis y su contenido
        # tokenizer = RegexpTokenizer(r'\w+')
        # token = tokenizer.tokenize(token)
        # token = token[:500]
        # tags = StanfordPOSTagger(self.model, path_to_jar=self.jar, encoding='utf8').tag(token)

        nlp = StanfordCoreNLP(r'C:\stanford-corenlp-full-2018-02-27', lang='es')
        tags = nlp.pos_tag(text)
        nlp.close()

        text_tagged = ''
        for item in tags:
            text_tagged += item[0] + '/' + item[1] + ' '

        return text_tagged
        # token = string.decode('utf-8')
        # token = nltk.word_tokenize(token)
        # tags =  nltk.pos_tag(token)
        # return tags

    @staticmethod
    def filter_tags(tags):
        final_words = []
        for i in tags:
            word = i[0]
            tag = i[1]
            if tag == 'ao0000' or tag == 'aq0000' or tag == 'nc00000' or tag == 'nc0n000' or tag == 'nc0p000' or tag == 'nc0s000' or tag == 'np00000':
                final_words.append(word)
        return final_words

    @staticmethod
    def cleanhtml(raw_html):
        # return BeautifulSoup(raw_html).text
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext

    @staticmethod
    def elimina_tildes(s):
        # s = s.decode('utf-8')
        return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))
