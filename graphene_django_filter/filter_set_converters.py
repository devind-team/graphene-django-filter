"""Functions for converting a FilterSet class to a tree and then to an input type."""

from typing import List, Optional, Sequence, Type

from anytree import Node
from django_filters import FilterSet


def sequence_to_tree(values: Sequence[str]) -> Node:
    """Convert a sequence to a tree."""
    node: Optional[Node] = None
    for value in values:
        node = Node(value, parent=node)
    return node.root


def try_add_sequence(tree: Node, values: Sequence[str]) -> bool:
    """Try to add a sequence to a tree.

    Return a flag indicating whether the mutation was made.
    """
    if tree.name == values[0]:
        for child in tree.children:
            is_mutated = try_add_sequence(child, values[1:])
            if is_mutated:
                return True
        tree.children = (*tree.children, sequence_to_tree(values[1:]))
        return True
    else:
        return False


def filter_set_to_trees(filter_set: Type[FilterSet]) -> List[Node]:
    """Convert a FilterSet class to a tree."""
    trees: List[Node] = []
    for filter_value in filter_set.base_filters.values():
        values = (*filter_value.field_name.split('__'), filter_value.lookup_expr)
        if len(trees) == 0 or not any([try_add_sequence(tree, values) for tree in trees]):
            trees.append(sequence_to_tree(values))
    return trees
