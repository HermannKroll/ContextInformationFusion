import pickle
import os
import matplotlib.pyplot as plt
from model.knowledgegraph import kg_verify_facts


def load_metadata_for_docs(conn_meta, query, split_metadata=False):
    """
    loads the metadata for documents
    @param conn_meta: connection to the database which includes PubMed metadata
    @param query: the query to contain metadata (must project pmid and metadata)
    @param split_metadata: if true the metadata attribute is first split and afterwise stored as a set
    @return: a dict mapping a pmid to a set of metadata values
    """
    cur = conn_meta.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    doc2meta = {}
    for r in rows:
        pmid, metadata = str(r[0]), str(r[1])

        if split_metadata:
            metadata = metadata.lower().split()
        else:
            # to avoid automatic splitting in sets
            metadata = [metadata]

        if pmid not in doc2meta:
            doc2meta[pmid] = set()
        doc2meta[pmid].update(metadata)

    return doc2meta


def jaccard(set1, set2):
    """
    computes the jaccard coefficient between two sets
    @param set1: first set
    @param set2: second set
    @return: the jaccard coefficient
    """
    if len(set1) == 0 or len(set2) == 0:
        return 0
    inter = len(set1.intersection(set2))
    return inter / (len(set1) + len(set2) - inter)


def compute_jaccard_sim_for_derived_facts(idx_subject, idx_object, fact2docs_for_rel1, fact2docs_for_rel2, doc2metadata):
    """
    computes the jaccard coefficient on-the-fly while deriving facts
    @param idx_subject: subject index of the first relation
    @param idx_object: object index of the second relation
    @param fact2docs_for_rel1: dict which maps each fact (s,o) pair of the first relation to a set of pmid's
    @param fact2docs_for_rel2: dict which maps each fact (s,o) pair of the second relation to a set of pmid's
    @param doc2metadata: dict which maps a pmid to a set of metadata values
    @return: a dict which stores for each derived fact (s,o) pair the maximum jaccard index achieved by current metadata
    """
    fact2maxjaccard = {}
    idx_object_len = len(idx_object)
    i = 0
    doc_contexts = 0
    for o1, subs1 in idx_object.items():
        i += 1
        print('deriving facts.. [{} / {}]\r'.format(i, idx_object_len), end="")
        if o1 in idx_subject:
            # join over all s1 and o2
            for o2 in idx_subject[o1]:
                for s1 in subs1:
                    # s1 and o2 should not be equal (e.g. can't cause itself)
                    if s1 == o2:
                        continue
                    # a fact can be derived from mutliple paths
                    new_fact = (s1, o2)

                    # get ids for both facts
                    docs1 = fact2docs_for_rel1[(s1, o1)]
                    docs2 = fact2docs_for_rel2[(o1, o2)] # o1 = s2

                    # compute jaccard for each document combination
                    max_jac = 0
                    for d1 in docs1:
                        # cannot be greater than 1.0
                        if max_jac >= 1.0:
                            break
                        for d2 in docs2:
                            if d1 == d2:
                                max_jac = 1.0
                                doc_contexts += 1
                                break

                            # no metadata available
                            if d1 not in doc2metadata or d2 not in doc2metadata:
                                continue

                            # compute jaccard between docs
                            current_jaccard = jaccard(doc2metadata[d1], doc2metadata[d2])
                            if current_jaccard > max_jac:
                                max_jac = current_jaccard

                    # set the max jaccard coefficient for the fact
                    if new_fact not in fact2maxjaccard:
                        fact2maxjaccard[new_fact] = max_jac
                    else:
                        current_jac = fact2maxjaccard[new_fact]
                        if max_jac > current_jac:
                            fact2maxjaccard[new_fact] = max_jac

    print('deriving facts.. [{} / {}]'.format(i, idx_object_len))
    print('{} doc contexts are used'.format(doc_contexts))
    return fact2maxjaccard


def load_kg_facts_with_doc_index(conn, query):
    """
    loads facts from the database and creates a fact2docs index
    fact2docs is a dict which maps a fact (s,o) pair to a list of pmids
    @param conn: SemMedDB connection
    @param query: query which projects pmid, subj and obj
    @return: a subject index, an object index, fact2docs index (each fact is mapped to a list of pmids)
    """
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()

    idx_subject = {}
    idx_object = {}
    fact2docs = {}
    for r in rows:
        pmid, sub, obj = str(r[0]), str(r[1]), str(r[2])

        if sub not in idx_subject:
            idx_subject[sub] = set()
        idx_subject[sub].add(obj)

        if obj not in idx_object:
            idx_object[obj] = set()
        idx_object[obj].add(sub)

        # create fact2docs index
        fact = (sub, obj)
        if fact not in fact2docs:
            fact2docs[fact] = [pmid]
        else:
            fact2docs[fact].append(pmid)

    return idx_subject, idx_object, fact2docs


def get_filename_max_jaccard(experiment, metadata_type):
    """
    computes the filename storing the max_jaccard index
    @param experiment: experiment name (cause / ddi gene)
    @param metadata_type: postfix (metadata type)
    @return: filename of the resulting file
    """
    return os.path.join("preprocessed_context_compatibility", "fact2maxjaccard_{}_{}.pkl".format(experiment, metadata_type))


def preprocess_document_pairs_for_experiment(experiment, queries_for_metadata, requires_splitting,
                                             meta_conn, metadata_name,
                                             idx_subject, idx_object,
                                             fact2docs_for_rel1, fact2docs_for_rel2):
    """
    preprocesses the jaccard coefficient between the document pairs which can be used for a fact derivation
    @param experiment: experiment name (cause / ddi gene)
    @param queries_for_metadata: queries to obtain the metadata
    @param requires_splitting: list of boolean values whether the metadata needs to be splitted after querying
    @param meta_conn: connection to the metadata database
    @param metadata_name: name of the current metadata
    @param idx_subject: subject index of the first relation
    @param idx_object: object index of the second relation
    @param fact2docs_for_rel1: dict which maps each fact (s,o) pair of the first relation to a set of pmid's
    @param fact2docs_for_rel2: dict which maps each fact (s,o) pair of the second relation to a set of pmid's
    """
    i = 0
    for query in queries_for_metadata:
        fn_postfix = metadata_name[i]
        print('= ' *60)
        print('processing jaccard coefficient over metadata: {}'.format(fn_postfix))
        doc2metadata = load_metadata_for_docs(meta_conn, query, split_metadata=requires_splitting[i])

        fact2maxjaccard = compute_jaccard_sim_for_derived_facts(idx_subject, idx_object, fact2docs_for_rel1, fact2docs_for_rel2, doc2metadata)

        # storing data to file
        filename = get_filename_max_jaccard(experiment, fn_postfix)
        print('storing fact2maxjaccard to {} ...'.format(filename))
        with open(filename, 'wb') as f:
            pickle.dump(fact2maxjaccard, f)

        i += 1
        print('= ' *60)


def do_experiment_with_context_pairs(experiment, queries_for_metadata, metadata_name, thresholds_to_check, idx_correct):
    """
    performs a experiment based on context pairs
    @param experiment: the experiment name (cause / ddi gene)
    @param queries_for_metadata: queries to obtain the metadata
    @param metadata_name: name of the current metadata
    @param thresholds_to_check: list of thresholds which should be checked
    @param idx_correct: the ground truth relation
    @return: results as a dict (maps metadata_name to a a list consisting of no. correct results and no of obtained
    results for each threshold )
    """
    results = {}
    i = 0
    for query in queries_for_metadata:
        print('=' * 60)
        # storing data to file
        filename = get_filename_max_jaccard(experiment, metadata_name[i])

        print('loading data from file: {} ...'.format(filename))
        with open(filename, 'rb') as f:
            fact2maxjaccard = pickle.load(f)
        print('{} jaccard coefficients loaded'.format(len(fact2maxjaccard)))

        result_list = []
        for t in thresholds_to_check:
            print('checking threshold: {}'.format(t))
            # we need to build a result dict here
            idx_results = {}
            amount_facts_above_t = 0
            for fact, coeff in fact2maxjaccard.items():
                # check if the coefficient of the fact is above the threshold
                if coeff >= t:
                    amount_facts_above_t += 1
                    s, o = fact
                    if s not in idx_results:
                        idx_results[s] = [o]
                    else:
                        idx_results[s].append(o)

            # we can verify the facts now
            correct_amount = kg_verify_facts(idx_correct, idx_results)
            result_list.append((correct_amount, amount_facts_above_t))
            print('{} of {} derived facts are correct'.format(correct_amount, amount_facts_above_t))

        results[metadata_name[i]] = result_list
        i += 1
        print('=' * 60)
    return results


def show_precision_recall_curve(results, kg_correct_facts, plot_name):
    """
    plots the results as as precision recall curve
    @param results: dict (maps metadata_name to a a list consisting of no. correct results and no of obtained
    results for each threshold )
    @param kg_correct_facts: no. of correct results (baseline for 100% recall)
    @param plot_name: filename to store the plot at
    """
    markers = ["ro--", "b^-.", "gs-", "x"]
    ax_r = [0, 1, 0, .75]
    converted_results = {}
    for metadata_type, res in results.items():
        print(metadata_type)
        prec_vals = []
        recall_vals = []

        # sort for recall
        res_sorted = sorted(res, key=lambda l: l[1], reverse=True)

        for correct_facts, obtained_facts in res_sorted:
            recall = correct_facts / kg_correct_facts
            recall_vals.append(recall)
            precision = correct_facts / obtained_facts
            prec_vals.append(precision)

        converted_results[metadata_type] = (prec_vals, recall_vals)

    plt.figure()
    plt.xlabel('recall')
    plt.ylabel('precision')
    plt.axis(ax_r)

    lines = []
    i = 0
    for k, v in converted_results.items():
        prec_vals, recall_vals = v
        line, = plt.plot(recall_vals, prec_vals, markers[i], label=k)
        lines.append(line)

        i += 1

    first_legend = plt.legend(handles=lines)
    plt.savefig(plot_name)
    plt.show()


def print_tab_seperated(results):
    """
    prints the resulting dict
    @param results: dict (maps metadata_name to a a list consisting of no. correct results and no of obtained
    results for each threshold )
    """
    for k, v in results.items():
        print(k)
        for correct, obtained in v:
            print('{}\t{}'.format(obtained, correct))
