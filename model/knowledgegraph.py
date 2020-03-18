

def kg_derive_facts(idx_subject, idx_object, compute_o_idx=False):
    """
    derives fact based on pattern matching inside the knowledge graph
    therefore the indices (subject -> [object1, ..., objectn] and object -> [sub1, ..., subn]
    are used
    @param idx_subject: dictionary which maps each subject of a relation to a list of objects
    @param idx_object: dictionary which maps each object of a relation to a list of subjects
    @param compute_o_idx: computes the reverse index in addition
    @return: a new index for the resulting relation (subject -> [obj1, ... objn])
    """
    results_idx_s = {}
    results_idx_o = {}
    amount = 0
    for o1, subs1 in idx_object.items():
        if o1 in idx_subject:
            # join over all s1 and o2
            for o2 in idx_subject[o1]:
                for s1 in subs1:
                    # s1 and s2 should not be equal (e.g. can't cause itself)
                    if s1 == o2:
                        continue

                    if s1 not in results_idx_s:
                        amount += 1
                        results_idx_s[s1] = set()
                        results_idx_s[s1].add(o2)
                    else:
                        # count only objects which are not included yet
                        if o2 not in results_idx_s[s1]:
                            amount += 1
                            results_idx_s[s1].add(o2)

                    if compute_o_idx:
                        if o2 not in results_idx_o:
                            results_idx_o[o2] = set()
                            results_idx_o[o2].add(s1)
                        else:
                            if s1 not in results_idx_o[o2]:
                                results_idx_o[o2].add(s1)

    if compute_o_idx:
        return results_idx_s, results_idx_o, amount
    return results_idx_s, amount


def kg_verify_facts(kg_idx_subject, results):
    """
    counts how many entries of the indexed relation are included in the kg (results)
    @param kg_idx_subject: the index of the relation to check
    @param results: the knowledge graph relation to check against
    @return: the number of correct results
    """
    correct = 0
    for sub, objects in results.items():
        if sub in kg_idx_subject:
            kg_objs = kg_idx_subject[sub]
            # check how many matching objects are included
            for o in objects:
                if o in kg_objs:
                    correct += 1
    return correct


def load_kg_facts(conn, query):
    """
    loads triple-based facts from a SemMedDB and builds the corresponding idx_subject and idx_object
    the indices store which (subject -> [object1, ..., objectn] and which object -> [sub1, ..., subn]
    @param conn: SemMedDB connection handle
    @param query: the query which retrieves facts from the database (must project pmid, subj and obj)
    @return: the corresponding idx_subject and idx_object
    """
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()

    idx_subject = {}
    idx_object = {}
    for r in rows:
        pmid, sub, obj = str(r[0]), str(r[1]), str(r[2])
        # print('"{}" __ "{}" __ "{}"'.format(pmid, sub, obj))
        if sub not in idx_subject:
            idx_subject[sub] = set()
        idx_subject[sub].add(obj)

        if obj not in idx_object:
            idx_object[obj] = set()
        idx_object[obj].add(sub)

    return idx_subject, idx_object

