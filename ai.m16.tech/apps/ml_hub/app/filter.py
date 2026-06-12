from ml_hub.app.ml_pipe import Node, NodeValue, VALUE_TYPE_STOP, VALUE_TYPE_EMPTY, VALUE_TYPE_OBJECT_DETECT, \
    VALUE_TYPE_MANY


class AndFilter(Node):
    def call(self, value: NodeValue):
        if value.type == VALUE_TYPE_MANY:
            for value in value.data:
                if value.type == VALUE_TYPE_STOP:
                    return value
        return value

    def string(self) -> str:
        return 'AndFilter'


class ClassFilter(Node):
    class_index: int

    def __init__(self, class_index: int):
        self.class_index = class_index

    def call(self, value: NodeValue) -> NodeValue:
        if value.data == self.class_index:
            return value

        return NodeValue(type=VALUE_TYPE_EMPTY)

    def string(self) -> str:
        return 'ClassFilter(' + str(self.class_index) + ')'


class ObjectClassFilter(Node):
    name: str

    def __init__(self, name: str):
        self.name = name

    def call(self, value: NodeValue) -> NodeValue:
        new_value = NodeValue(type=VALUE_TYPE_OBJECT_DETECT, data=[])
        for item in value.data:
            if item.name == self.name:
                new_value.data.append(item)
        return new_value

    def string(self) -> str:
        return 'ObjectClassFilter(' + self.name + ')'


class ObjectPositionFilter(Node):
    x1: int
    y1: int
    x2: int
    y2: int

    def __init__(self, x1: int, y1: int, x2: int, y2: int):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    def call(self, value: NodeValue) -> NodeValue:
        items = []
        for item in value.data:
            if item.point_1.x >= self.x1 and item.point_1.y >= self.y1 and \
                    item.point_2.x <= self.x2 and item.point_2.y <= self.y2:
                items.append(item)

        if len(items) == 0:
            return NodeValue(type=VALUE_TYPE_STOP)

        return NodeValue(type=VALUE_TYPE_OBJECT_DETECT, data=items)

    def string(self) -> str:
        return f'ObjectPositionFilter({self.x1}, {self.y1}, {self.x2}, {self.y2})'
