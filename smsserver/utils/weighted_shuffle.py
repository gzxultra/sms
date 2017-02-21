# coding: utf-8
import random

__all__ = ('weighted_shuffle',)


class Node(object):

    def __init__(self, value=None, weight=None, left=None, right=None):
        self.value = value
        self.weight = weight
        self.left = left
        self.right = right

    def is_leaf(self):
        return self.left is None and self.right is None


def _weighted_node(a, b):
    """
    生成 a, b 两个节点的父节点

    a.weight/(a.weight+b.weight) 的概率 a 在 b 的左边
    b.weight/(a.weight+b.weight) 的概率 b 在 a 的左边
    """
    total = a.weight + b.weight
    r = random.uniform(0, total)
    if r < a.weight:
        return Node(None, total, left=a, right=b)
    else:
        return Node(None, total, left=b, right=a)


def _tree(choices):
    length = len(choices)
    if length == 0:
        return None
    elif length == 1:
        value, weight = choices[0]
        return Node(value, weight)
    else:
        middle = int(length/2)
        return _weighted_node(_tree(choices[:middle]), _tree(choices[middle:]))


def _flatten(tree):
    if tree is None:
        return []
    if tree.is_leaf():
        return [tree.value]
    return _flatten(tree.left) + _flatten(tree.right)


def weighted_shuffle(choices):
    """
    按一定的权重打乱元素的顺序

    Args:
        choices: (value, weight) 组成的列表
    Returns:
        打乱顺序后的 value 列表
    """
    return _flatten(_tree(choices))
