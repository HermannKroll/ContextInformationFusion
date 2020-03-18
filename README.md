# Context-Compatible Information Fusion for Knowledge Graphs
This repository belongs to our TPDL2020 submission, Context-Compatible Information Fusion for Knowledge Graphs.
The repository provides our scripts and links to our precomputed data.
The project builds upon SemMedDB as a medical knowledge graph. Therefore, you need to setup SemMedDB first.
Besides, all results are reported in an Excel sheet (Experiments on SemMed2019.xlsx).


## Setting up SemMedDB
We use SemMedDB as a PostgreSQL database. The following steps will help you to setup SemMedDB.
### Downloading SemMedDB
Download the predication table from *[SemMed NIH](https://skr3.nlm.nih.gov/SemMedDB/download/download.html)*. We use SemMedDB in version semmedVER40_R. You can directly download the predication table at *[Predication](https://skr3.nlm.nih.gov/SemMedDB/download/semmedVER40_R_PREDICATION.sql.gz)*.
Rename the file to predication.sql

### Setup Postgres
We use SemMedDB as a PostgreSQL V10 database in our experimental setup and scripts. Details for PostgreSQL can be found at *[PostgreSQL](https://www.postgresql.org/)*
We recommend to setup a PostgresSQL database. We name the database "semmeddb". We have written a script to convert the MySQL SQL-statements to PostgreSQL (located in sql directory).
```
python3 sql/semmed_postgres_converter.py predication.sql predication.psql
```
Subsequently, we use "psql" to load our sql scripts. 
Create the predication table and load the data into it.
```
psql -d semmeddb < sql/semmed_create_table.sql 
psql -d semmeddb < sql/predication.psql
```
Finally, create indexes and materialized views for our experiments (this may take a while).
```
psql -d semmeddb < sql/semmed_create_index.sql
psql -d semmeddb < sql/materialized_views.sql
```

# Experiments
The experiments belonging to our first experiment (knowledge graph without contexts and with strict contexts) can be found in 01-KG_Context.ipynb.
Experiments belomnging to our second experiment (context compatibility) can be found in 02-Context_Compatibility.ipynb.
To rerun our experiments, you need to setup a python environment.

## Setting up Python 
We provide Jupyter notebooks for our experiments. You can run them in an Jupyter environment with the following packages installed:
```
pip install psycopg2 nltk scikit-learn matplotlib
```

## Library Graph vs Knowledge Graph
For the first experiment, you need to enter your database credentials for semmeddb in the beginning of the Jupyter notebook. 

## Context Compatibility
For the second experiment, you need access to the metadata of PubMed. To bypass setting up a metadata database, you can find our precomputed metadata simiarity values and clusterings at *[OneDrive](https://1drv.ms/u/s!ArDgbq3ak3Zuh5gBfAQQDkrb9_2Zbg?e=jbP0uX)*. Download the zip archiv and unzip it. The files should be stored as an additional directory (inside this repository) called:
```
preprocessed_context_compatibility
```

Next, you can rerun the second notebook without having metadata database credentials entered. This line ensures that the metadata processing will be skipped.
```
do_preprocessing = False
```

Thanks for reading!