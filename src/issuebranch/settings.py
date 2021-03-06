import os

ON_DECK_COLUMN_NAME = "on deck"
PARKING_LOT_NAME = "parking lot"

PRODUCT_BACKLOG_NAME = "product backlog"
SCRUM_BOARD_NAME = os.environ.get("DEFAULT_BOARD_NAME", "Kanban Board")
DEFAULT_COLUMN_NAME = os.environ.get("DEFAULT_COLUMN_NAME", "to do")

OTHER_PROJECT = {
    PRODUCT_BACKLOG_NAME: SCRUM_BOARD_NAME,
    SCRUM_BOARD_NAME: PRODUCT_BACKLOG_NAME,
}
