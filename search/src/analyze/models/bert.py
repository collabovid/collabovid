from transformers.modeling_bert import BertModel
from transformers.modeling_bert import BertPreTrainedModel


class BertForPooling(BertPreTrainedModel):
    def __init__(self, config):
        super().__init__(config)

        self.bert = BertModel(config)

        self.init_weights()

    def forward(self, features):
        output_states = self.bert(**features)
        output_tokens = output_states[0]
        cls_tokens = output_tokens[:, 0, :]  # CLS token is first token
        features.update({'token_embeddings': output_tokens, 'cls_token_embeddings': cls_tokens,
                         'attention_mask': features['attention_mask']})

        if len(output_states) > 2:
            features.update({'all_layer_embeddings': output_states[2]})
        return features
