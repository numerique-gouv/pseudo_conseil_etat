# model = SequenceTagger.load('/home/pavel/etalab/code/conseil_etat/models/baseline_ner/final-model.pt')
import textract
from flair.data import Sentence
from string import ascii_uppercase

from flair.models import SequenceTagger
from flair.embeddings import TokenEmbeddings, StackedEmbeddings, CharacterEmbeddings, FlairEmbeddings, BertEmbeddings, \
    CamembertEmbeddings

replacements = ["{}...".format(letter) for letter in ascii_uppercase]


def load_text(doc_path):
    return textract.process(doc_path, encoding='utf-8').decode("utf8")


def predict_tags(text, tagger):
    sentence = Sentence(text)
    tagger.predict(sentence)
    return sentence.to_dict(tag_type='ner')["entities"]


def clean_tags(tags):
    return tags


def build_pseudonymisation_map(tags):
    pseudonymisation_map = {}
    tags = clean_tags(tags)
    for ent in tags:
        if ent["confidence"] > 0.7 and ent["type"] in ["LOC", "PER"] and len(ent["text"].strip()) > 2:  # Cleaner

            if ent["text"].strip() in pseudonymisation_map:
                pseudonymisation_map[ent["text"].strip()]["pos"].append((ent["start_pos"], ent["end_pos"]))
            else:
                pseudonymisation_map[ent["text"].strip()] = {
                    "replacement": replacements.pop(0),
                    "pos": [(ent["start_pos"], ent["end_pos"])]
                }
    return pseudonymisation_map


def pseudonimize_text(pseudonymisation_map, text):
    # dégeu à refaire

    for entity in pseudonymisation_map:
        replacement = pseudonymisation_map[entity]["replacement"]
        text = text.replace(entity, replacement)

    return text


def save_file(text):
    text_file = open("sample.txt", "w")
    n = text_file.write(text)
    text_file.close()


def main(path, tagger):
    text = load_text(path)
    save_file(pseudonimize_text(build_pseudonymisation_map(predict_tags(text, tagger)), text))


def convert_to_conll():
    pass


if __name__ == '__main__':
    path = "/Users/thomasclavier/Documents/Projects/Etalab/prod/pseudo_conseil_etat/src/database/IN/DCA/CAA13/2013/20130215/10MA01447.doc"
    tagger = SequenceTagger.load('fr-ner')

    main(path, tagger)
