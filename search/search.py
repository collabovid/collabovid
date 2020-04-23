class PaperWithScore:
    def __init__(self, paper, score):
        self._paper = paper
        self.score = score

    @property
    def paper(self):
        return self._paper


class Search:
    def __init__(self, *args, **kwargs):
        pass

    def find(self):
        raise NotImplementedError()

