class TextToChunksSplitter:

    def __init__(self, chunk_size=50, overlap=10):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split_into_chunks(self, text):
        splitted_text = []
        words = text.split()

        if len(words) // self.chunk_size > 0:
            n = len(words) // self.chunk_size
        else:
            n = 1
        for w in range(n):
            if w == 0:
                current_chunk = words[:self.chunk_size+self.overlap]
                splitted_text.append(" ".join(current_chunk))
            else:
                current_chunk = words[w * self.chunk_size:
                                         w * self.chunk_size +
                                         self.chunk_size + self.overlap]

                splitted_text.append(" ".join(current_chunk))

        return splitted_text
