from ml_hub.app.ml_pipe import Node, NodeValue, VALUE_TYPE_IMAGE


class CropImage(Node):
    x: int
    y: int

    height: int
    width: int

    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def call(self, value: NodeValue) -> NodeValue:
        # self.log('x: %s, y: %s' % (self.x, self.y))
        data = value.data[self.y:self.y + self.height, self.x:self.x + self.width]
        new_value = NodeValue(type=VALUE_TYPE_IMAGE, data=data)

        return new_value

    def string(self) -> str:
        return f'CropImage({self.x}, {self.y}, {self.width}, {self.height})'
