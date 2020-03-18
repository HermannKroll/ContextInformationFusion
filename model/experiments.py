from model.knowledgegraph import kg_verify_facts
from model.librarygraph import derive_facts_with_context, derive_facts_ddi_function


def do_cause_experiment_with_context(idx_context, idx_correct):
    """
    computes the cause experiment
    @param idx_context: the cause relation behind a context layer
    @param idx_correct: the cause relation as ground truth
    @return: number of correct obtained results, number of obtained results
    """
    print('deriving new facts...')
    cause_results, cause_results_len = derive_facts_with_context(idx_context, idx_context, idx_context)
    print('{} facts derived'.format(cause_results_len))

    print('verifying facts in semmeddb...')
    cause_correct = kg_verify_facts(idx_correct, cause_results)

    print('{} of {} derived facts are correct'.format(cause_correct, cause_results_len))
    del cause_results
    return cause_correct, cause_results_len


def do_ddi_gene_experiment_with_context(idx_context_dg, idx_context_gd, ddi_gen_idx_subjects_correct):
    """
    computes the ddi gene experiment
    @param idx_context_dg: the drug-gene relation behind a context layer
    @param idx_context_gd: the gene-drug relation behind a context layer
    @param ddi_gen_idx_subjects_correct: ground truth of correct interactions
    @return: number of correct obtained results, number of obtained results
    """
    print('deriving new facts...')
    ddi_gen_results, ddi_gen_res_amounts = derive_facts_with_context(idx_context_dg, idx_context_dg, idx_context_gd)
    print('{} facts derived'.format(ddi_gen_res_amounts))

    print('verifying facts in semmeddb...')
    ddi_gen_correct = kg_verify_facts(ddi_gen_idx_subjects_correct, ddi_gen_results)

    print('derived {} of {} derived facts are correct'.format(ddi_gen_correct, ddi_gen_res_amounts))
    del ddi_gen_results
    return ddi_gen_correct, ddi_gen_res_amounts


def do_ddi_function_experiment_with_context(idx_context_dg, idx_context_gf, ddi_gen_idx_subjects_correct):
    """
    computes the ddi function experiment
    @param idx_context_dg: the drug-gene relation behind a context layer
    @param idx_context_gf: the gene-function relation behind a context layer
    @param ddi_gen_idx_subjects_correct: ddi_gen_idx_subjects_correct: ground truth of correct interactions
    @return: number of correct obtained results, number of obtained results
    """
    print('deriving new facts drug-gene-function-gene-drug ...')
    # drug is in both cases the object
    ddi_f_res, ddi_f_res_len = derive_facts_ddi_function(idx_context_dg, idx_context_dg, idx_context_gf)
    print('{} facts derived'.format(ddi_f_res_len))

    print('verifying facts in semmeddb...')
    ddi_f_correct = kg_verify_facts(ddi_gen_idx_subjects_correct, ddi_f_res)
    print('{} of {} derived facts are correct'.format(ddi_f_correct, ddi_f_res_len))
    del ddi_f_res
    return ddi_f_correct, ddi_f_res_len