import os
import sys
import textract
import subprocess

import pandas as pd
import src.data.xml2conll as x2c

from glob import glob
from joblib import Parallel, delayed
from tqdm import tqdm

from src.data.doc2txt import doc2txt
from src.tools.utils import available_cpu_count

n_jobs = available_cpu_count()


# TODO: Bouger ces fonctions ailleurs

def create_work_folders(database_path="/database"):
    path = os.getcwd()
    print("The current working directory is %s" % path)
    new_path = path + database_path
    access_rights = 0o755

    if not os.path.isdir(new_path):
        try:
            os.mkdir(new_path, access_rights)
        except OSError:
            print("Creation of the directory %s failed" % new_path)
        else:
            print("Successfully created the directory %s" % new_path)
            return (new_path)

    else:
        print("Directory %s already exists" % new_path)
        return (new_path)


def create_txt_files(convert_missing=False, n_jobs=n_jobs):
    doc_files_path = create_work_folders()
    # TODO: Modifier le retour du path
    # TODO: CP pour copier les fichiers au bon endroit
    convert_missing = False  # Modifier pour prendre en paramètre

    doc_paths = []

    if not os.path.isdir(doc_files_path) and os.path.isfile(doc_files_path):
        doc_paths = [doc_files_path]
    else:
        doc_paths = glob(doc_files_path + "/**/*.doc", recursive=True)
    if not doc_paths:
        raise Exception("Path not found")

    if convert_missing:
        transformed_docs_ids = [p[:-4] for p in glob(doc_files_path + "**/*.txt", recursive=True)]
        doc_paths_ids = [p[:-4] for p in doc_paths]
        doc_paths = list(set.difference(set(doc_paths_ids), transformed_docs_ids))
        doc_paths = [p + ".doc" for p in doc_paths]

    if n_jobs < 2:
        job_output = []
        for doc_path in tqdm(doc_paths):
            tqdm.write(f"Converting file {doc_path}")
            job_output.append(doc2txt(doc_path))
    else:
        job_output = Parallel(n_jobs=n_jobs)(delayed(doc2txt)(doc_path) for doc_path in tqdm(doc_paths))


def get_correct_line(df_decisions):
    """
    The passed df has repeated lines for the same file (same chemin_source).
    We take the most recent one.
    :param df_decisions: Dataframe of decisions
    :return: Dataframe without repeated lines (according to the chemin_source column)
    """
    return df_decisions.sort_values('timestamp_modification').drop_duplicates('chemin_source', keep='last')


def get_data(df_decision):

    source_path = (df_decision["chemin_source"]).replace("\\", "/")  # Windows path -> Linux path cool hack

    # TODO : Deal with manuel paths

    if "manuel" in source_path:
        source_path = "/".join(source_path.split("/")[1:]).lower()
        decision_file_id = os.path.splitext(os.path.basename(source_path))[0]
    else:
        source_path = "/".join(source_path.split("/")[3:])  # Remove server name from path
        decision_file_id = os.path.splitext(os.path.basename(source_path))[0]

    annotations_xml = df_decision["detail_anonymisation"]
    doc_path = os.path.join("database/", source_path)
    txt_path = doc_path[:-4] + ".txt"  # gère mal les docx
    print(txt_path)
    if os.path.isfile(txt_path):
        # # We check that the folder exists. No sense in having an annotation XML file without the decision .doc
        # if not os.path.exists(doc_path):
        #     #logger.debug(f"File {doc_path} not found !!")
        #     return 0
        xml_path = os.path.join("database/", os.path.dirname(source_path), decision_file_id + ".xml")
        with open(xml_path, "w", encoding="utf-16") as xmlo:
            # logger.info(f"Saving XML file as {xml_path}")
            xmlo.write(annotations_xml)

        return xml_path
    elif os.path.isfile(doc_path):
        print("ready to transform")
        return "kill"
    else:
        print("no file")
        return "kill"

def generate_conll_files(df):

    if n_jobs < 2:
        # job_output = []
        # for annotation_xml_path in tqdm(annotation_xml_paths):
        #     job_output.append(run(annotation_xml_path))
        pass
    else:
        job_output = Parallel(n_jobs=n_jobs)(
            delayed(x2c.run)(get_data(row)) for index, row in tqdm(df.iterrows()))

    # Get correctly processed paths
    processed_fine = [f"{c[1]}\n" for c in job_output if c[0] == 1]
    with open("./logs/correct_xmls.txt", "w") as filo:
        filo.writelines(processed_fine)

    # logger.info(
    #     f"{len(processed_fine)} XML/DOC files were treated and saved as CoNLL. "
    #     f"{len(job_output) - len(processed_fine)} files had some error.")


if __name__ == '__main__':

    def process_file(row):

        source_path = (row["chemin_source"]).replace("\\", "/")  # Windows path -> Linux path cool hack

        if "manuel" in source_path:
            source_path = "/".join(source_path.split("/")[1:]).lower()
            decision_file_id = os.path.splitext(os.path.basename(source_path))[0]
        else:
            source_path = "/".join(source_path.split("/")[3:])  # Remove server name from path
            decision_file_id = os.path.splitext(os.path.basename(source_path))[0]


        if os.path.isfile("database/" + source_path):
            # text = textract.process("database/" + source_path, encoding='utf-8').decode("utf8")
            # row["valid"] = True
            # row["text"] = text
            # row["local_path"] = source_path

            # TODO: piste a investiguer ^

            xml_path = "clean_data/" + str(row["id"]) + ".xml"
            with open(xml_path, "w", encoding="utf-16") as xmlo:
                xmlo.write(row["detail_anonymisation"])

            txt_path = "clean_data/" + str(row["id"]) + ".txt"
            subprocess.check_call(["textutil", "-convert", "txt", "database/" + source_path, "-output", txt_path])
            # with open(txt_path, "w", encoding="utf-8") as txto:
            #     txto.write(text)

            x2c.run(xml_path, txt_path)
        else:
            row["valid"] = False



        return row



    #params
    only_corriges = True
    tagged_folder_path = "database/"

    df_decisions = pd.read_csv("database/documents.csv")
    if only_corriges:
        df_decisions = df_decisions[df_decisions.statut == 5]
    df_decisions = get_correct_line(df_decisions)
    df_decisions = df_decisions.sample(n=100)

    df_decisions["valid"] = False
    df_decisions["text"] = None
    df_decisions["local_path"] = None

    job_output = Parallel(n_jobs=n_jobs)(delayed(process_file)(row) for index, row in tqdm(df_decisions.iterrows()))




    # if n_jobs < 2:
    #     # job_output = []
    #     # for annotation_xml_path in tqdm(annotation_xml_paths):
    #     #     job_output.append(run(annotation_xml_path))
    #     pass
    # else:
    #     job_output = Parallel(n_jobs=n_jobs)(
    #         delayed(x2c.run)(get_data(row)) for index, row in tqdm(df.iterrows()))

    # Get correctly processed paths
    # processed_fine = [f"{c[1]}\n" for c in job_output if c[0] == 1]
    # with open("./logs/correct_xmls.txt", "w") as filo:
    #     filo.writelines(processed_fine)

    # logger.info(
    #     f"{len(processed_fine)} XML/DOC files were treated and saved as CoNLL. "
    #     f"{len(job_output) - len(processed_fine)} files had some error.")

