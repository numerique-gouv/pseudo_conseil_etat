.ONESHELL:
SHELL=/bin/bash
CONDA_ACTIVATE=source $$(conda info --base)/etc/profile.d/conda.sh ; conda activate ; conda activate
.PHONY: transform_docs create_xml create_conll create_dataset train_model
transform_docs: 
	$(CONDA_ACTIVATE) conseil_etat
	python src/data/doc2txt.py /data/conseil_etat/final_test/IN_2020
create_xml:
	$(CONDA_ACTIVATE) conseil_etat
	python src/data/table2xml.py /data/conseil_etat/final_test/ano_2020.csv
create_conll:
	$(CONDA_ACTIVATE) conseil_etat
	python -m src.data.xml2conll /data/conseil_etat/final_test/IN_2020
create_dataset:
	$(CONDA_ACTIVATE) conseil_etat
	python src/data/create_dataset.py /data/conseil_etat/final_test/IN_2020 /data/conseil_etat/final_test/conll_dataset
train_model:
	$(CONDA_ACTIVATE) conseil_etat
	python -m src.models.flair_baseline_model.py