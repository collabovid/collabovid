from termcolor import colored


class LogColor:
    """
    Allows for different log colors. The given message will be translated into a html object if its written
    to the database or to the terminal if its written to stdout.
    """
    def __init__(self, message):
        self._message = message

    @property
    def message(self):
        return self._message

    @property
    def color(self):
        raise NotImplementedError()

    @property
    def terminal_message(self):
        return colored(self.message, self.color)

    @property
    def database_message(self):
        return "<span class='{}'>{}</span>".format(self.color, self.message)


class Green(LogColor):
    @property
    def color(self):
        return 'green'


class Red(LogColor):
    @property
    def color(self):
        return 'red'


class Blue(LogColor):
    @property
    def color(self):
        return 'blue'


class Gray(LogColor):
    @property
    def color(self):
        return 'blue'