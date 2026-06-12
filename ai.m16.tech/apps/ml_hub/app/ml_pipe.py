from dataclasses import dataclass
from abc import abstractmethod
from typing import List

VALUE_TYPE_EMPTY = 'empty'
VALUE_TYPE_STOP = 'stop'
VALUE_TYPE_INT = 'int'
VALUE_TYPE_STRING = 'string'
VALUE_TYPE_IMAGE = 'image'
VALUE_TYPE_OBJECT_DETECT = 'object_detect'
VALUE_TYPE_MANY = 'object_many'


@dataclass
class NodeValue:
    type: str
    data: any = None


class Node:
    @abstractmethod
    def call(self, value: NodeValue):
        pass

    @abstractmethod
    def string(self) -> str:
        pass

    def log(self, mes: str):
        print(self.__class__.__name__, mes)


class PipeNode(Node):
    nodes: List[Node]

    def __init__(self, nodes: List[Node]):
        self.nodes = list(nodes)

    def call(self, value: NodeValue):
        if value.type == VALUE_TYPE_STOP:
            return value

        for item in self.nodes:
            value = item.call(value)
            if value.type == VALUE_TYPE_STOP:
                return value
        return value

    def string(self) -> str:
        items_str = ", ".join([item.string() for item in self.nodes])
        return "PipeNode(" + items_str + ")"


class ParallelNode(Node):
    nodes: List[Node]

    def __init__(self, nodes: List[Node]):
        self.nodes = nodes

    def call(self, value=None):
        if value.type == VALUE_TYPE_STOP:
            return value
        values = []
        for node in self.nodes:
            node_value = node.call(value)
            values.append(node_value)
        return NodeValue(type=VALUE_TYPE_MANY, data=values)

    def string(self) -> str:
        items_str = ", ".join([item.string() for item in self.nodes])
        return "ParallelNode(" + items_str + ")"


class MapNode(Node):
    last_value_type = ''

    def __init__(self, source, node: Node):
        self.source = source
        self.node = node

    def call(self, value: NodeValue = None):
        value_list = self.source.call(NodeValue(type=VALUE_TYPE_EMPTY))
        for value in value_list:
            res_value = self.node.call(value)
            if res_value.type != self.last_value_type:
                self.last_value_type = res_value.type
                if res_value.type == VALUE_TYPE_STOP:
                    print('stop')

        return NodeValue(type=VALUE_TYPE_EMPTY)

    def string(self) -> str:
        return "MapNode(" + self.node.string() + ")"


def ml_pipe(*args):
    nodes = list(args)
    return PipeNode(nodes)


def ml_parallel(*args):
    nodes = list(args)
    return ParallelNode(nodes)


def ml_map(source, node: Node):
    return MapNode(source, node)


def ml_run(node: Node):
    print('node', type(node))
    print(node.string())
    node.call(NodeValue(type=VALUE_TYPE_EMPTY))
