class QueueMessage:
    def __init__(self, type_="NotSet", text=""):
        self._type = type_
        self._text = text

    def getType(self):
        return self._type

    def setType(self, type_):
        self._type = type_

    def getText(self):
        return self._text

    def setText(self, text):
        self._text = text
