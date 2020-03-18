from model.knowledgegraph import kg_derive_facts


def load_lg_facts(conn, query):
    """
    loads triple-based facts from a SemMedDB and builds the corresponding idx_pmid
    idx_pmid stores a idx_subject and a idx_object for each pmid from the query result
    the indices store which (subject -> [object1, ..., objectn] and which object -> [sub1, ..., subn]

    @param conn: SemMedDB connection handle
    @param query: the query which retrieves facts from the database (must project pmid, subj and obj)
    @return: the idx_pmid (which stores a idx_subject and idx_object behind each pmid)
    """
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()

    idx_pmid = {}
    for r in rows:
        pmid, sub, obj = str(r[0]), str(r[1]), str(r[2])

        if pmid not in idx_pmid:
            idx_s = {}
            idx_o = {}
            idx_pmid[pmid] = {"idx_subject": idx_s, "idx_object": idx_o}
        else:
            idx_s = idx_pmid[pmid]["idx_subject"]
            idx_o = idx_pmid[pmid]["idx_object"]

        if sub not in idx_s:
            idx_s[sub] = set()
        idx_s[sub].add(obj)

        if obj not in idx_o:
            idx_o[obj] = set()
        idx_o[obj].add(sub)

    return idx_pmid


def merge_2_into_1(res1, res2):
    """
    merges 2 dictionaries together
    the second dictionary is merged in the first one (the second remains unchanged / is copied)
    @param res1: a dictionary in which the second dict will be merges
    @param res2: second dict will remain unchanged
    @return: the first dict (in which the second dict is merged)
    """
    res = res1
    for s, objects in res2.items():
        if s not in res:
            res[s] = objects.copy()
        else:
            res[s].update(objects)
    return res


def count_val_size_in_dict(result):
    """
    expects a dict with keys which map to lists
    sums the size of all lists in the dict
    @param result: a dict where each key maps to a list
    @return: the summed size of all lists
    """
    amount = 0
    for k, values in result.items():
        amount += len(values)
    return amount


def derive_facts_with_context(context, relation1, relation2):
    """
    derives facts like the kg but limited to contexts
    @param context: the context index stores a set of key sas the contexts
    @param relation1: first relation to derive facts (each key maps to a idx_sub and idx_obj)
    @param relation2: second relation to derive facts (each key maps to a idx_sub and idx_obj)
    @return: the resulting relation (also behind a context layer), the number of results
    """
    results_s_merged = {}
    for c in context:
        # context must be included in both relations
        if c not in relation1 or c not in relation2:
            continue

        idx_s = relation2[c]["idx_subject"]
        idx_o = relation1[c]["idx_object"]

        c_results, c_result_len = kg_derive_facts(idx_s, idx_o)

        results_s_merged = merge_2_into_1(results_s_merged, c_results)

    return results_s_merged, count_val_size_in_dict(results_s_merged)


def derive_facts_ddi_function(context, relation1, relation2):
    """
    derives facts for the ddi function experiment (the temporary join table must be kept in between)
    @param context: the context index stores a set of key sas the contexts
    @param relation1: first relation to derive facts (each key maps to a idx_sub and idx_obj)
    @param relation2: second relation to derive facts (each key maps to a idx_sub and idx_obj)
    @return: the resulting relation (also behind a context layer), the number of results
    """
    results_s_merged = {}
    for c in context:
        # context must be included in both relations
        if c not in relation1 or c not in relation2:
            continue

        idx_s = relation2[c]["idx_subject"]
        idx_o = relation1[c]["idx_object"]

        _, ddi_f_t1_df_o, t1_len = kg_derive_facts(idx_s, idx_o, compute_o_idx=True)

        # drug is in both cases the object
        ddi_f_res, ddi_f_res_len = kg_derive_facts(ddi_f_t1_df_o, ddi_f_t1_df_o)
        results_s_merged = merge_2_into_1(results_s_merged, ddi_f_res)

    return results_s_merged, count_val_size_in_dict(results_s_merged)


