--mv_cause
CREATE MATERIALIZED VIEW mv_cause AS ( WITH S1 AS (
	SELECT P1.pmid, P1.subject_cui, P1.object_cui FROM public.predication P1
	WHERE P1.predicate = 'CAUSES'
	AND P1.pmid NOT LIKE'%[%'
	), S2 AS (
	SELECT S1.subject_cui, S1.object_cui, count(*) AS amount FROM S1
	GROUP BY S1.subject_cui, S1.object_cui
	) SELECT DISTINCT S2.subject_cui, S2.object_cui, S2.amount, S1.pmid FROM S2, S1
	WHERE S1.subject_cui = S2.subject_cui
	AND S1.object_cui = S2.object_cui
) WITH DATA;

--mv_cause_2 (amount > 2)
CREATE MATERIALIZED VIEW mv_cause_2 AS ( SELECT *
	FROM mv_cause
	WHERE amount > 2 ) WITH DATA;


--------------------------------------------------------------------------------------------------------------------------------
-- DDI Correct Results
CREATE MATERIALIZED VIEW mv_ddi_correct AS (
	SELECT subject_cui as d1, object_cui as drug2 FROM PREDICATION WHERE predicate = 'INTERACTS_WITH'
	UNION ALL
	SELECT object_cui as d1, subject_cui as drug2 FROM PREDICATION WHERE predicate = 'INTERACTS_WITH'
) WITH DATA;

SELECT COUNT(*) FROM (SELECT d1, drug2 FROM mv_ddi_correct) S;

--------------------------------------------------------------------------------------------------------------------------------
-- DDI over gene
-- mv_ddi_gen
CREATE MATERIALIZED VIEW mv_ddi_gen AS (
	SELECT P1.pmid, P1.subject_cui, P1.predicate, P1.object_cui, P1.subject_semtype, P1.object_semtype
			FROM public.predication P1 WHERE (
			(
			(P1.predicate = 'INHIBITS' OR P1.predicate = 'STIMULATES' OR P1.predicate =
			'INTERACTS_WITH') AND
			(P1.object_semtype = 'gngm' OR P1.object_semtype = 'aapp') AND (P1.subject_semtype = 'clnd' OR P1.subject_semtype = 'phsu' OR P1.subject_semtype =
			'sbst')
			) OR (
			(P1.predicate = 'INHIBITS' OR P1.predicate = 'STIMULATES' OR P1.predicate =
			'INTERACTS_WITH') AND
			(P1.subject_semtype = 'gngm' OR P1.subject_semtype = 'aapp') AND (P1.object_semtype = 'clnd' OR P1.object_semtype = 'phsu' OR P1.object_semtype =
			'sbst')
			) )
			AND P1.pmid NOT LIKE'%[%' )
WITH DATA;



--------------------------------------------------------------------------------------------------------------------------------
-- DDI over function
-- mv_ddi_function
CREATE MATERIALIZED VIEW mv_ddi_function AS (
	WITH
	S1 AS (
		SELECT P1.pmid, P1.subject_cui, P1.predicate, P1.object_cui, P1.subject_semtype, P1.object_semtype
		FROM public.predication P1 WHERE (
		(
		(P1.predicate = 'INHIBITS' OR P1.predicate = 'STIMULATES' OR P1.predicate =
		'INTERACTS_WITH') AND
		(P1.object_semtype = 'gngm' OR P1.object_semtype = 'aapp') AND (P1.subject_semtype = 'clnd' OR P1.subject_semtype = 'phsu' OR P1.subject_semtype =
		'sbst')
		) OR (
		(P1.subject_semtype = 'gngm' OR P1.subject_semtype = 'aapp') AND
		(P1.predicate = 'AFFECTS' OR P1.predicate = 'AUGMENTS' OR P1.predicate = 'CAUSES' OR P1.predicate = 'DISRUPTS' OR P1.predicate =
		'PREDISPOSES') AND
		(P1.object_semtype = 'biof' OR P1.object_semtype = 'phsf' OR P1.object_semtype =
		'orgf' OR P1.object_semtype = 'menp'
		OR P1.object_semtype = 'ortf' OR P1.object_semtype = 'celf' OR P1.object_semtype =
		'moft' OR P1.object_semtype = 'genf'

		OR P1.object_semtype = 'patf' OR P1.object_semtype = 'dsyn' OR P1.object_semtype = 'mobd' OR P1.object_semtype = 'neop'
		OR P1.object_semtype = 'comd' OR P1.object_semtype = 'emod') )
		)
		AND P1.pmid NOT LIKE'%[%'
	),
	S2 AS (
		SELECT S1.subject_cui, S1.predicate, S1.object_cui, S1.subject_semtype,
		S1.object_semtype, count(*) AS amount FROM S1
		GROUP BY S1.subject_cui, S1.predicate, S1.object_cui, S1.subject_semtype, S1.object_semtype
	)

	SELECT DISTINCT S2.subject_cui, S2.predicate, S2.object_cui, S2.subject_semtype, S2.object_semtype, S2.amount, S1.pmid
		FROM S2, S1
		WHERE S1.subject_cui = S2.subject_cui AND S1.predicate = S2.predicate
		AND S1.object_cui = S2.object_cui
		AND S1.subject_semtype = S2.subject_semtype AND S1.object_semtype = S2.object_semtype
	)
WITH DATA;

