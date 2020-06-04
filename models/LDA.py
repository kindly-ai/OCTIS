from models.model import Abstract_Model
import numpy as np
from gensim.models import ldamodel
import gensim.corpora as corpora


class LDA_Model(Abstract_Model):

    hyperparameters = {
        'corpus': None,
        'num_topics': 100,
        'id2word': None,
        'distributed': False,
        'chunksize': 2000,
        'passes': 1,
        'update_every': 1,
        'alpha': 'symmetric',
        'eta': None,
        'decay': 0.5,
        'offset': 1.0,
        'eval_every': 10,
        'iterations': 50,
        'gamma_threshold': 0.001,
        'minimum_probability': 0.01,
        'random_state': None,
        'ns_conf': None,
        'minimum_phi_value': 0.01,
        'per_word_topics': False,
        'callbacks': None}

    id2word = None
    id_corpus = None
    dataset = None

    def info(self):
        return {
            "citation": r"""
@inproceedings{DBLP:conf/nips/BleiNJ01,
  author    = {David M. Blei and
               Andrew Y. Ng and
               Michael I. Jordan},
  editor    = {Thomas G. Dietterich and
               Suzanna Becker and
               Zoubin Ghahramani},
  title     = {Latent Dirichlet Allocation},
  booktitle = {Advances in Neural Information Processing Systems 14 [Neural Information
               Processing Systems: Natural and Synthetic, {NIPS} 2001, December 3-8,
               2001, Vancouver, British Columbia, Canada]},
  pages     = {601--608},
  publisher = {{MIT} Press},
  year      = {2001},
  url       = {http://papers.nips.cc/paper/2070-latent-dirichlet-allocation},
  timestamp = {Thu, 12 Mar 2020 11:31:34 +0100},
  biburl    = {https://dblp.org/rec/conf/nips/BleiNJ01.bib},
  bibsource = {dblp computer science bibliography, https://dblp.org}
}
            """,
            "name": "LDA, Latent Dirichlet Allocation"
        }

    def train_model(self, dataset, hyperparameters={}, topics=10,
                    topic_word_matrix=True, topic_document_matrix=True,
                    use_partitions=True, update_with_test=False):
        """
        Train the model and return output

        Parameters
        ----------
        dataset : dataset to use to build the model
        hyperparameters : hyperparameters to build the model
        topics : if greather than 0 returns the most significant words
                 for each topic in the output
                 Default True
        topic_word_matrix : if True returns the topic word matrix in the output
                            Default True
        topic_document_matrix : if True returns the topic document
                                matrix in the output
                                Default True

        Returns
        -------
        result : dictionary with up to 3 entries,
                 'topics', 'topic-word-matrix' and 
                 'topic-document-matrix'
        """
        partition = []
        if use_partitions:
            partition = dataset.get_partitioned_corpus()

        if self.id2word == None:
            self.id2word = corpora.Dictionary(dataset.get_corpus())

        if self.id_corpus == None:
            self.id_corpus = [self.id2word.doc2bow(
                document) for document in dataset.get_corpus()]

        if self.dataset == None:
            self.dataset = dataset

        self.hyperparameters.update(hyperparameters)
        hyperparameters = self.hyperparameters

        # Allow alpha to be a float in case of symmetric alpha
        if isinstance(self.hyperparameters["alpha"], float):
            self.hyperparameters["alpha"] = [
                self.hyperparameters["alpha"]
            ] * self.hyperparameters["num_topics"]

        self.trained_model = ldamodel.LdaModel(
            corpus=self.id_corpus,
            id2word=self.id2word,
            num_topics=hyperparameters["num_topics"],
            distributed=hyperparameters["distributed"],
            chunksize=hyperparameters["chunksize"],
            passes=hyperparameters["passes"],
            update_every=hyperparameters["update_every"],
            alpha=hyperparameters["alpha"],
            eta=hyperparameters["eta"],
            decay=hyperparameters["decay"],
            offset=hyperparameters["offset"],
            eval_every=hyperparameters["eval_every"],
            iterations=hyperparameters["iterations"],
            gamma_threshold=hyperparameters["gamma_threshold"],
            minimum_probability=hyperparameters["minimum_probability"],
            random_state=hyperparameters["random_state"],
            ns_conf=hyperparameters["ns_conf"],
            minimum_phi_value=hyperparameters["minimum_phi_value"],
            per_word_topics=hyperparameters["per_word_topics"],
            callbacks=hyperparameters["callbacks"])

        result = {}

        if topic_word_matrix:
            result["topic-word-matrix"] = self.trained_model.get_topics()

        if topics > 0:
            result["topics"] = self._get_topics_words(topics)

        if topic_document_matrix:
            result["topic-document-matrix"] = self._get_topic_document_matrix()

        if use_partitions:
            new_corpus = [self.id2word.doc2bow(
                document) for document in partition[1]]
            if update_with_test:
                self.trained_model.update(new_corpus)

                if topic_word_matrix:
                    result["test-topic-word-matrix"] = self.trained_model.get_topics()

                if topics > 0:
                    result["test-topics"] = self._get_topics_words(topics)

                if topic_document_matrix:
                    result["test-topic-document-matrix"] = self._get_topic_document_matrix()

            else:
                test_document_topic_matrix = []
                for document in new_corpus:
                    test_document_topic_matrix.append(
                        self.trained_model[document])
                result["test-document-topic-matrix"] = test_document_topic_matrix

        return result

    def _get_topics_words(self, topk):
        """
        Return the most significative words for each topic.
        """
        topic_terms = []
        for i in range(self.hyperparameters["num_topics"]):
            topic_words_list = []
            for word_tuple in self.trained_model.get_topic_terms(i, topk):
                topic_words_list.append(self.id2word[word_tuple[0]])
            topic_terms.append(topic_words_list)
        return topic_terms

    def _get_topic_document_matrix(self):
        """
        Return the topic representation of the
        corpus
        """
        doc_topic_tuples = []
        for document in self.dataset.get_corpus():
            doc_topic_tuples.append(self.trained_model.get_document_topics(
                self.id2word.doc2bow(document)))

        topic_document = np.zeros((
            self.hyperparameters["num_topics"],
            len(doc_topic_tuples)))

        for ndoc in range(len(doc_topic_tuples)):
            document = doc_topic_tuples[ndoc]
            for topic_tuple in document:
                topic_document[topic_tuple[0]][ndoc] = topic_tuple[1]
        return topic_document
