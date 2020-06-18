import os
import torch
import torch.nn as nn
from transformers import BertConfig
from .bert import BertForPooling
from .pooling import Pooling

MODEL_CLASSES = {
    'bert': (BertForPooling, BertConfig)
}


class EmbeddingHead(nn.Module):
    def __init__(self, input_dimension, embedding_dimension):
        super(EmbeddingHead, self).__init__()
        self.projection = nn.Linear(input_dimension, embedding_dimension)

    def forward(self, x):
        return self.projection(x)


class PaperEmbeddingModel(nn.Module):
    def __init__(self, model_path=None, model_type='longformer', model_name=None, vocab_length=None, embedding_size=512,
                 pooling_mode_cls_token: bool = False,
                 pooling_mode_max_tokens: bool = False,
                 pooling_mode_mean_tokens: bool = True,
                 pooling_mode_mean_sqrt_len_tokens: bool = False,
                 use_head=True):
        super(PaperEmbeddingModel, self).__init__()

        if model_type not in MODEL_CLASSES:
            raise ValueError("Unknown model type: " + model_type)
        else:
            model_cls, config_cls = MODEL_CLASSES[model_type]

        if model_path is None:
            config = config_cls.from_pretrained(model_name)
            self.transformer = model_cls.from_pretrained(model_name, config=config)
            self.transformer.resize_token_embeddings(vocab_length)
            self.pooling = Pooling(word_embedding_dimension=config.hidden_size,
                                   pooling_mode_cls_token=pooling_mode_cls_token,
                                   pooling_mode_max_tokens=pooling_mode_max_tokens,
                                   pooling_mode_mean_tokens=pooling_mode_mean_tokens,
                                   pooling_mode_mean_sqrt_len_tokens=pooling_mode_mean_sqrt_len_tokens)
        else:
            config = config_cls.from_pretrained(model_path)
            self.transformer = model_cls.from_pretrained(model_path, config=config)
            self.pooling = Pooling.load(model_path)

        self.use_head = use_head
        self.embedding_size = embedding_size

        if use_head:
            self.embedding_head = EmbeddingHead(input_dimension=self.pooling.pooling_output_dimension,
                                                embedding_dimension=embedding_size)
            if model_path is not None:
                self.embedding_head.load_state_dict(
                    torch.load(os.path.join(model_path, 'embedding_head.pt'), map_location=torch.device('cpu')))

    def forward(self, features):
        x = self.transformer(features)
        x = self.pooling(x)
        if self.use_head:
            x = self.embedding_head(x)
        return x

    def embedding_dimension(self):
        if self.use_head:
            return self.embedding_size
        else:
            return self.pooling.pooling_output_dimension

    @staticmethod
    def from_pretrained(model_name, *args, **kwargs):
        return PaperEmbeddingModel(model_name=model_name, *args, **kwargs)

    @staticmethod
    def from_saved_model(model_path, model_type='longformer'):
        return PaperEmbeddingModel(model_path=model_path, model_type=model_type)

    def save(self, path):
        os.makedirs(path, exist_ok=True)
        self.transformer.save_pretrained(path)
        self.pooling.save(path)
        if self.use_head:
            torch.save(self.embedding_head.state_dict(), os.path.join(path, 'embedding_head.pt'))
