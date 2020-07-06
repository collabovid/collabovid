import cld3


class LanguageDetector():
    def detect(self, query):
        lang_prediction = cld3.get_language(query)
        return lang_prediction