from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import TruncatedSVD

import pickle
import os

import nltk
import re

from model.librarygraph import merge_2_into_1


# load nltk's SnowballStemmer as variabled 'stemmer'
from nltk.stem.snowball import SnowballStemmer

# load nltk's English stopwords as variable called 'stopwords'
stopwords = nltk.corpus.stopwords.words('english')
stemmer = SnowballStemmer("english")


def load_txt_for_docs(conn_meta, query):
    """
    loads texts for documents
    @param conn_meta: connection to the metadata database
    @param query: query to obtain the text for a pubmed doc
    @return: a dict which maps a pmid to a string
    """
    cur = conn_meta.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    doc2meta = {}
    for r in rows:
        pmid, txt = str(r[0]), str(r[1])

        if pmid not in doc2meta:
            doc2meta[pmid] = txt
        else:
            raise Exception('do not expect documents to have multiple texts')

    return doc2meta


def combine_document_clusters(context_clusters, idx_pmid):
    """
    combines all documents in a cluster to a knowledge graph
    @param context_clusters: a dict which maps a cluster label to a set of belonging pmids
    @param idx_pmid: library graph (each pmids maps to a idx_subject and idx_object)
    @return: a dict which maps a cluster label to a combined relations (alls facts in this cluster are combined)
    """
    idx_context_compatib = {}
    cluster_id = 0
    cluster_size = len(context_clusters)
    for c, docs in context_clusters.items():
        print('computing context clusters... [{} / {}]\r'.format(cluster_id, cluster_size), end="")
        c_idx_s = {}
        c_idx_o = {}
        # go trough all docs in a cluster
        for d in docs:
            if d in idx_pmid:
                merge_2_into_1(c_idx_s, idx_pmid[d]["idx_subject"])
                merge_2_into_1(c_idx_o, idx_pmid[d]["idx_object"])
        idx_context_compatib[cluster_id] = {"idx_subject": c_idx_s, "idx_object": c_idx_o}
        cluster_id += 1

    print('computing context clusters... [{} / {}]'.format(cluster_id, cluster_size))
    return idx_context_compatib


def tokenize_and_stem(text):
    """
    applies tokenization and stemming to the texts
    thanks to http://brandonrose.org/clustering
    @param text: a string
    @return: the stemmed version of the string
    """
    # here I define a tokenizer and stemmer which returns the set of stems in the text that it is passed
    # first tokenize by sentence, then by word to ensure that punctuation is caught as it's own token
    tokens = [word for sent in nltk.sent_tokenize(text) for word in nltk.word_tokenize(sent)]
    filtered_tokens = []
    # filter out any tokens not containing letters (e.g., numeric tokens, raw punctuation)
    for token in tokens:
        if re.search('[a-zA-Z]', token):
            filtered_tokens.append(token)
    stems = [stemmer.stem(t) for t in filtered_tokens]
    return stems


def cluster_documents(tfidf, doc2txt, k):
    """
    applies a MiniBatchKMeans with k-means++ algorithm to the tfidf matrix
    @param tfidf: a tfidf matrix
    @param doc2txt: dict which maps pmids to txt (pmids are necessary to compute the resulting clusters)
    @param k: k determines the amount of clusters
    @return: a dict which maps a cluster label to a list of belonging pmids
    """
    print('computing KMeans clustering...')
    kmeans = MiniBatchKMeans(  # KMeans(
        n_clusters=k, init='k-means++',
        n_init=10, max_iter=300)
    kmeans.fit(tfidf)

    print('assigning clusters...')
    docs = list(doc2txt.keys())
    cluster2docs = {}
    i = 0
    for l in kmeans.labels_:
        if l not in cluster2docs:
            cluster2docs[l] = [docs[i]]
        else:
            cluster2docs[l].append(docs[i])
        i += 1
    print('documents clustered into {} clusters'.format(len(cluster2docs)))
    return cluster2docs


def get_cluster_filename(filename_prefix, k):
    """
    computes the filename of the cluster file
    @param filename_prefix: experiment name and text type (e.g. cause_title)
    @param k: k determines the amount of clusters
    @return: the filenname
    """
    return os.path.join("preprocessed_context_compatibility", '{}.k{}.pkl'.format(filename_prefix, k))


def preprocess_and_dump_clustering(conn_meta, query, filename_prefix, clusters_to_check):
    """
    computes the clustering for a specific txts as an preprocessing step and stores the results into a file
    @param conn_meta: connection to the metadata database
    @param query: query to obtain the txts
    @param filename_prefix: experiment name and metadata name
    @param clusters_to_check: a list of k values which should be used for clustering
    """
    print('loading txt for documents...')
    doc2txt = load_txt_for_docs(conn_meta, query)
    print('{} documents with txts loaded'.format(len(doc2txt)))

    # convert dictonary to a list of txts
    all_txt = list(doc2txt.values())
    print('computing tfidf matrix...')
    tfidf_vectorizer = TfidfVectorizer(max_df=0.8, max_features=200000,
                                       min_df=3, stop_words='english',
                                       use_idf=True, tokenizer=tokenize_and_stem)

    tfidf = tfidf_vectorizer.fit_transform(all_txt)
    # compute pca
    truncated_svd = TruncatedSVD(n_components=300)
    principal_components = truncated_svd.fit_transform(tfidf)

    for k in clusters_to_check:
        print('=' * 60)
        cluster2docs = cluster_documents(principal_components, doc2txt, k=k)
        filename = get_cluster_filename(filename_prefix, k)
        print('storing {} context clusters into {}'.format(k, filename))
        with open(filename, 'wb') as f:
            pickle.dump(cluster2docs, f)
        print('=' * 60)


def load_dumped_clusters(clustering_type, k):
    """
    loads the stored cluster from a file
    @param clustering_type: the prefix (experiment and metadata_name)
    @param k: k value
    @return: a dict which maps a cluster label to a list of pmids
    """
    filename = get_cluster_filename(clustering_type, k)
    cluster2docs = {}
    print('load cluster contexts from {}...'.format(filename))
    with open(filename, 'rb') as f:
        cluster2docs = pickle.load(f)
    print('{} cluster contexts are loaded'.format(len(cluster2docs)))
    return cluster2docs


