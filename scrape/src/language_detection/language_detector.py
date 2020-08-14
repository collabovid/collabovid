import cld3


class LanguageDetector():
    """
    Uses Googles CLD3 to detect language of given text.
    """

    def detect(self, query):
        lang_prediction = cld3.get_language(query)
        return lang_prediction