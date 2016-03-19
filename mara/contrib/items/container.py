"""
Container mixin for stores which hold items
"""
from __future__ import unicode_literals

from collections import defaultdict

from ... import storage

__all__ = ['ItemContainerMixin']


class ContainerError(Exception):
    """Unable to comply"""


class CannotContain(Exception):
    """This cannot contain items"""


class NotFound(Exception):
    """Item not found"""


class TooManyFound(Exception):
    """Found more than one item by that name"""


class ItemContainerMixin(storage.Store):
    """
    Mixin for a store so it can contain items
    """
    abstract = True

    # If can_contain, can contain other objects
    can_contain = True

    # List of items
    items = storage.Field(list)

    # Make exceptions available on the class for convenience
    ContainerError = ContainerError
    CannotContain = CannotContain
    NotFound = NotFound
    TooManyFound = TooManyFound

    def add_item(self, item):
        if not self.can_contain:
            raise CannotContain()
        self.items.append(item)
        self.save()

    def remove_item(self, item):
        if not self.can_contain:
            raise CannotContain()
        self.items.remove(item)
        self.save()

    def _find_item(self, name, recurse):
        """
        Search this item (and optionally recurse) for the named item

        Return a tuple of (singular, plural), containing singular and plural
        matches
        """
        singular = []
        plural = []
        for item in self.items:
            if name == item.name:
                singular.append(item)
            elif name == item.plural:
                plural.append(item)

            if recurse and item.can_contain:
                child_singles, child_plurals = item.find_item(name, recurse)
                singular.extend(child_singles)
                plural.extend(child_plurals)
        return singular, plural

    def find_item(self, name, recurse=False):
        """
        Search this item (and optionally recurse) for the named item
        Returns a list of items
        """
        singular, plural = self._find_item(name, recurse)

        if singular:
            # If we've found a single or more, also consider the plurals
            singular.extend(plural)
        elif plural:
            # If we've only found plurals user must have been searching for all
            return plural

        # ++ Logic check here
        '''
        if not singular:
            raise NotFound()
        elif len(singular) > 1:
            raise TooManyFound()
        '''

        return singular

    def get_items_display(
        self, filter_cls=None, depth=0, indent=0, indent_size=0, prose=False
    ):
        """
        Return a list of formatted and nested item strings suitable to display,
        optionally filtered by issubclass, and optionally recurse any container
        items and list their children too.

        If an item is recursed, its entry in the returned list will be a tuple
        of (item, children), where children is a list of items and tuples of
        deeper containers.

        If the container holds more than one item with the same string value,
        they will be counted together, eg "3 red balloons".

        Arguments:
            filter_cls
                Only return items that are subclasses of this
                (argument used directly in issubclass).

                Default: None

            depth
                Depth of any child items to list, with 0 meaning no children,
                1 direct descendants, 2 children and grandchildren etc.

                Use a negative depth to list all descendants without limit.

                Default: 0 (no children)

            indent
                Number of space characters to start this line with. Used
                internally when recursing, but can be used to give an indent to
                the top level of items.

                Default: 0

            indent_size
                Size of each indent, in characters.

                Default: 2

            prose
                If True, list items using "an" or "a" instead of 1
        """
        # Make dict of items item description strings
        # {item_str: [(children, count), ...] }
        descs = defaultdict(list)
        articles = {}
        plurals = {}
        for item in self.items:
            # Filter by class
            if filter_cls and not issubclass(item, filter_cls):
                continue

            # Recurse containers to specified depth
            children = []
            if depth != 0 and issubclass(item, ItemContainerMixin):
                # Get children at correct indent
                children = item.get_items(
                    filter_cls=filter_cls, depth=depth - 1,
                    indent=indent + indent_size, indent_size=indent_size,
                )

            # Store articles and plurals
            item_str = item.name
            articles[item_str] = item.article
            plurals[item_str] = item.plural

            # Now store children and count
            added = False
            if item_str in descs:
                for (children2, count), i in enumerate(descs[item_str]):
                    if children == children2:
                        descs[i] = (children2, count + 1)
                        added = True
                        break
            if not added:
                descs[item_str].append((children, 1))

        # Now render the strings alphabetically with indent
        lines = []
        for item_str in sorted(descs.keys()):
            # Add in their children, sorted by number of parent items,
            # then number of children
            for children, count in sorted(
                descs[item_str],
                key=lambda (children, count): (count, len(children)),
            ):
                lines.append('%(indent)s%(count)s %(item_str)s' % {
                    'indent': ' ' * indent,
                    'count': (
                        articles[item_str] if prose and count == 1 else count
                    ),
                    'item_str': (
                        item_str if count == 1 else plurals[item_str]
                    ),
                })
                lines.extend(children)

        return lines