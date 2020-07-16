import torch


class SlidingWindowTokenizer():

    def __init__(self, tokenizer, max_length=512, device='cpu', overlap=128, max_windows=4):
        self._tokenizer = tokenizer
        self._max_length = max_length
        self._device = device
        self._overlap = overlap
        self._max_windows = max_windows

    def tokenize(self, texts):
        tokenizer_args = dict(pad_to_max_length=True, truncation=True, add_special_tokens=True,
                              max_length=self._max_length, return_overflowing_tokens=True,
                              return_tensors='pt',
                              stride=self._overlap)
        result = {'input_ids': [], 'token_type_ids': [], 'attention_mask': []}
        index_array = []
        end_index = 0
        for text in texts:
            tokens = self._tokenizer(text, **tokenizer_args)
            for key in result.keys():
                result[key].append(tokens[key].to(self._device))
            end_index += 1
            while 'overflowing_tokens' in tokens:
                end_index += 1
                input_tokens = self._tokenizer.convert_ids_to_tokens(tokens['overflowing_tokens'][0].tolist())
                tokens = self._tokenizer(input_tokens, **tokenizer_args, is_pretokenized=True)
                for key in result.keys():
                    result[key].append(tokens[key].to(self._device))

                # only allow max windows due to memory limits
                if (end_index - (index_array[-1] if len(index_array) > 0 else 0)) >= self._max_windows:
                    break

            index_array.append(end_index)

        for key in result.keys():
            result[key] = torch.cat(result[key], dim=0)
        return result, index_array
