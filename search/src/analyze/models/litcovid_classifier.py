from transformers import (
    AutoTokenizer,
    LongformerConfig
)
import torch.nn.functional
from src.analyze.models.longformer import LongformerForSequenceClassification
from src.analyze.models.utils import batch_iterator
import torch

# the 8 litcovid categories
categories = ['general', 'mechanism', 'transmission', 'diagnosis', 'treatment', 'prevention', 'case-report',
              'forecasting']


class LitcovidMultiLabelClassifier():

    def __init__(self, model_path_or_name, device='cuda'):
        """
        Creates a new LitcovidMultiLabelClassifier from a given model path or name.
        :param model_path_or_name: A model name or the path to the saved model
        :param device: which device to use. For example 'cpu' or 'cuda'
        """
        self.tokenizer = AutoTokenizer.from_pretrained(model_path_or_name)
        self.config = LongformerConfig.from_pretrained(model_path_or_name, num_labels=len(categories))
        self.config.sep_token_id = 2
        self.config.attention_window = 32
        self.model = LongformerForSequenceClassification.from_pretrained(model_path_or_name, config=self.config)

        self.max_sequence_length = 640
        self.device = device
        self.model.to(device)
        self.model.eval()

    def _tokenize(self, inputs):
        """
        tokenize the input texts
        :param inputs: list of strings or list of tuples of str
        :return: the tokens
        """
        tokens = self.tokenizer.batch_encode_plus(inputs, add_special_tokens=True, return_tensors='pt',
                                                  pad_to_max_length=True, return_attention_masks=True,
                                                  max_length=self.max_sequence_length)
        for key in list(tokens.keys()):
            tokens[key] = tokens[key].to(self.device)
        return tokens

    def prediction_iterator(self, paper_iterator, batch_size=1):
        """
        Receives an iterator over papers and yields for each paper, the paper and a dict with the categories
        and corresponding predictions
        :param paper_iterator: An iterator that yields objects that have a 'title' and a 'abstract' property
        :param batch_size: The batch size that should be used when evaluating the underlying model
        :return:
        """
        for papers in batch_iterator(paper_iterator, batch_size=batch_size):
            input = [(paper.title, paper.abstract) for paper in papers]
            tokens = self._tokenize(input)
            with torch.no_grad():
                logits = self.model(**tokens)[0]
                probabilities = torch.nn.functional.sigmoid(logits).detach().cpu().numpy()
                for paper, distribution in zip(papers, probabilities):
                    yield paper, {categories[idx]: prob.item() for idx, prob in enumerate(distribution)}
