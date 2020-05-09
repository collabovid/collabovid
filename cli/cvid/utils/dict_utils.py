import copy

class DictUtils:

    @staticmethod
    def merge_dicts(dict1, dict2):
        dict1 = copy.deepcopy(dict1)
        dict2 = copy.deepcopy(dict2)
        if not isinstance(dict1, dict) or not isinstance(dict2, dict):
            return dict2
        for k in dict2:
            if k in dict1:
                dict1[k] = DictUtils.merge_dicts(dict1[k], dict2[k])
            else:
                dict1[k] = dict2[k]
        return dict1