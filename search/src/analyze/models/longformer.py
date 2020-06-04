from torch.nn import CrossEntropyLoss, MSELoss, BCEWithLogitsLoss
import torch
import torch.nn as nn

from transformers.modeling_bert import BertPreTrainedModel
from transformers.configuration_longformer import LongformerConfig
from transformers.modeling_longformer import LongformerModel, _compute_global_attention_mask


class LongformerClassificationHead(nn.Module):
    """Head for sentence-level classification tasks."""

    def __init__(self, config):
        super().__init__()
        self.dense = nn.Linear(config.hidden_size, config.hidden_size)
        self.dropout = nn.Dropout(config.hidden_dropout_prob)
        self.out_proj = nn.Linear(config.hidden_size, config.num_labels)

    def forward(self, features, **kwargs):
        x = features[:, 0, :]  # take <s> token (equiv. to [CLS])
        x = self.dropout(x)
        x = self.dense(x)
        x = torch.tanh(x)
        x = self.dropout(x)
        x = self.out_proj(x)
        return x


class LongformerForSequenceClassification(BertPreTrainedModel):
    config_class = LongformerConfig
    base_model_prefix = "longformer"

    def __init__(self, config):
        super().__init__(config)
        self.num_labels = config.num_labels

        self.longformer = LongformerModel(config)
        self.classifier = LongformerClassificationHead(config)

        self.init_weights()

    def forward(
            self,
            input_ids=None,
            attention_mask=None,
            global_attention_mask=None,
            token_type_ids=None,
            position_ids=None,
            inputs_embeds=None,
            labels=None,
    ):

        # set global attention on question tokens
        if global_attention_mask is None:
            # put global attention on all tokens until `config.sep_token_id` is reached
            global_attention_mask = _compute_global_attention_mask(input_ids, self.config.sep_token_id)
            # global attention on cls token
            global_attention_mask[:, 0] = 1

        attention_mask = attention_mask.to(torch.uint8)

        outputs = self.longformer(
            input_ids,
            attention_mask=attention_mask,
            global_attention_mask=global_attention_mask,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            inputs_embeds=inputs_embeds,
        )

        sequence_output = outputs[0]
        logits = self.classifier(sequence_output)
        outputs = (logits,) + outputs[2:]
        if labels is not None:
            if self.num_labels == 1:
                #  We are doing regression
                loss_fct = MSELoss()
                loss = loss_fct(logits.view(-1), labels.view(-1))
            elif labels.dim() == 1:
                loss_fct = CrossEntropyLoss()
                loss = loss_fct(logits.view(-1, self.num_labels), labels.view(-1))
            elif labels.dim() == 2:
                # we are doing multi label classification
                loss_fct = BCEWithLogitsLoss()
                loss = loss_fct(logits.view(-1, self.num_labels), labels.view(-1, self.num_labels))
            else:
                raise ValueError(f"Wrong shape of labels: {labels.size()}")

            outputs = (loss,) + outputs
        return outputs  # (loss), logits, (hidden_states), (attentions)
