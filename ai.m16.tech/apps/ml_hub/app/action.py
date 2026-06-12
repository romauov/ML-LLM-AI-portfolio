from ml_hub.app.ml_pipe import Node, NodeValue, VALUE_TYPE_EMPTY


class ActionSendMessage(Node):
    number_person = 0

    def call(self, value=None):
        number_person = len(value.data)
        if self.number_person != number_person:
            self.number_person = number_person
            print('SendMessage', len(value.data))

        return NodeValue(type=VALUE_TYPE_EMPTY)

    def string(self) -> str:
        return 'ActionSendMessage'
