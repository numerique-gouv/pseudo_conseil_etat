from flair.data import Corpus
from flair.embeddings import TokenEmbeddings, WordEmbeddings, StackedEmbeddings, CharacterEmbeddings, FlairEmbeddings, \
    CamembertEmbeddings, BertEmbeddings, PooledFlairEmbeddings
from typing import List
import torch

from src.utils import Monitor

torch.manual_seed(42)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False
import numpy as np
np.random.seed(0)
from flair.data import Corpus
from flair.datasets import ColumnCorpus


def create_flair_corpus(data_folder):
    # define columns
    columns = {0: 'text', 1: 'ner'}

    # init a corpus using column format, data folder and the names of the train, dev and test files
    corpus: Corpus = ColumnCorpus(data_folder, columns,
                                  train_file='train.txt',
                                  test_file='test.txt',
                                  dev_file='dev.txt')
    return corpus

# 1. get the corpus
data_folder = '/data/conseil_etat/train_dev_test/69_8_10/'

corpus: Corpus = create_flair_corpus(data_folder)
print(corpus)

# 2. what tag do we want to predict?
tag_type = 'ner'

# 3. make the tag dictionary from the corpus
tag_dictionary = corpus.make_tag_dictionary(tag_type=tag_type)
print(tag_dictionary.idx2item)


# 4. initialize embeddings
embedding_types: List[TokenEmbeddings] = [

    WordEmbeddings('fr'),

    # comment in this line to use character embeddings
    # CharacterEmbeddings(),

    # comment in these lines to use flair embeddings
    # PooledFlairEmbeddings('fr-forward'),
    # FlairEmbeddings('fr-backward'),

    # bert embeddings
    # BertEmbeddings('bert-base-multilingual-cased')
    # CamembertEmbeddings()
    # CCASS Flair Embeddings FWD
    # FlairEmbeddings('/data/embeddings_CCASS/flair_language_model/jurinet/best-lm.pt'),

    # CCASS Flair Embeddings BWD
    # FlairEmbeddings('/data/embeddings_CCASS/flair_language_model/jurinet/best-lm-backward.pt')
]
monitor = Monitor(50)
embeddings: StackedEmbeddings = StackedEmbeddings(embeddings=embedding_types)

# 5. initialize sequence tagger
from flair.models import SequenceTagger

tagger: SequenceTagger = SequenceTagger(hidden_size=100,
                                        embeddings=embeddings,
                                        tag_dictionary=tag_dictionary,
                                        tag_type=tag_type,
                                        rnn_layers=1,
                                        use_crf=True,
                                        )

# 6. initialize trainer
from flair.trainers import ModelTrainer

trainer: ModelTrainer = ModelTrainer(tagger, corpus)
trainer.num_workers = 8
# 7. start training
trainer.train('models/baseline_ner',
              learning_rate=0.1,
              mini_batch_size=8,
              max_epochs=5,
              embeddings_storage_mode="gpu")
monitor.stop()
# 8. plot weight traces (optional)
# from flair.visual.training_curves import Plotter
# plotter = Plotter()
# plotter.plot_weights('models/baseline_ner/weights.txt')