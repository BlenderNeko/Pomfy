from enum import Enum


SLOT_MIN_HEIGHT = 27
"""The minimum height of a node slot"""

SOCKET_RADIUS = 7
"""The visual radius a socket fits into."""

SOCKET_PADDING = 4
"""The amount of invisible padding used when deciding if the mouse is inside a socket."""


class SlotType(Enum):
    """Defines where the node socket on the slot should be positioned and behave."""

    INPUT = 1
    """The slot provides input for the node"""
    OUTPUT = 2
    """The slot defines output for the node"""
    BI = 3
    """The slot if bidirectional, only used for reroute nodes"""
    NONE = 4  # TODO: Implement
    """The slot has no socket"""


class SocketShape(Enum):
    """Defines the shape of a socket."""

    CIRCLE = 1
    HOLLOW_CIRCLE = 2
    DIAMOND = 3
    HOLLOW_DIAMOND = 4
    SQUARE = 5
    HOLLOW_SQUARE = 6


class ConnectionChangedType(Enum):
    REMOVED = 0
    ADDED = 1
    ALTERED = 2
