import functools
import logging

from issuebranch.backends.github import Backend, GithubSession

ON_DECK_COLUMN_NAME = 'on deck'
PARKING_LOT_NAME = 'parking lot'

PRODUCT_BACKLOG_NAME = 'product backlog'
SCRUM_BOARD_NAME = 'scrum board'

OTHER_PROJECT = {
    PRODUCT_BACKLOG_NAME: SCRUM_BOARD_NAME,
    SCRUM_BOARD_NAME: PRODUCT_BACKLOG_NAME,
}


class BaseHandler(object):
    def __init__(self, data):
        self.data = data

        self.session = GithubSession()


class IssueHandler(BaseHandler):
    """
    Handles issue actions
    """
    @property
    def logger(self):
        return logging.getLogger(f'{__name__}.{self.__class__.__name__}')

    def do_opened(self):
        """
        When an issue is opened add it to the parking lot
        """
        issue_number = self.data['issue']['number']
        issue_data = Backend(issue_number).issue

        product_backlog_data = self.session.get_project(PRODUCT_BACKLOG_NAME)
        parking_log_column_data = self.session.get_column(product_backlog_data, PARKING_LOT_NAME)

        self.session.create_card(parking_log_column_data, issue_data)

    def run(self):
        action = self.data['action']

        action_fn_name = f'do_{action}'
        action_fn = getattr(self, action_fn_name)
        if action_fn is None:
            self.logger.warning(f'no function found for action={action}')
            return

        action_fn()

class ProjectHandler(BaseHandler):
    """
    Handles project actions
    """
    def add_to_on_deck(self, column_data):
        # print(f'add_to_on_deck, column_data={column_data}')
        issue_url = self.project_card_data['content_url']
        project_data = self.get_request_data(column_data['project_url'])

        other_project_data = self.get_other_project_data(project_data)
        other_project_on_deck = self.get_project_on_deck(other_project_data)

        card = self.find_card(other_project_on_deck, issue_url)
        if card is None:
            issue_id = int(issue_url.rsplit('/', 1)[-1])
            issue_data = Backend(issue_id).issue

            self.session.create_card(other_project_on_deck, issue_data)

    def find_card(self, column_data, content_url):
        # look for the card in the other board's on deck
        for card in self.session.get_cards(column_data):
            if card['content_url'] == content_url:
                return card

    def get_other_project_data(self, project_data):
        other_project_name = OTHER_PROJECT.get(project_data['name'].lower())

        return self.session.get_project(other_project_name)

    def get_project_on_deck(self, project_data):
        return self.session.get_column(project_data, ON_DECK_COLUMN_NAME)

    @functools.lru_cache(maxsize=10)
    def get_request_data(self, url):
        return self.session.request('get', url).json()

    @property
    def project_card_data(self):
        return self.data['project_card']

    def run(self):
        action = self.data['action']
        if action != 'moved':
            return

        # check if something was added to the on deck column
        column_url = self.project_card_data['column_url']
        column_data = self.get_request_data(column_url)

        if column_data['name'].lower() == ON_DECK_COLUMN_NAME:
            self.add_to_on_deck(column_data)

            return

        # check if something was removed from the on deck column

        # replace the url in the column url with the from column to see if the card was removed from on deck
        from_column_url = column_url.replace(str(self.project_card_data['column_id']), str(self.data['changes']['column_id']['from']))
        from_column_data = self.get_request_data(from_column_url)

        if from_column_data['name'].lower() == ON_DECK_COLUMN_NAME:
            self.remove_from_on_deck(from_column_data)

            return

    def remove_from_on_deck(self, column_data):
        # print(f'add_to_on_deck, column_data={column_data}')
        issue_url = self.project_card_data['content_url']
        project_data = self.get_request_data(column_data['project_url'])

        other_project_data = self.get_other_project_data(project_data)
        other_project_on_deck = self.get_project_on_deck(other_project_data)

        card_data = self.find_card(other_project_on_deck, issue_url)
        if card_data is not None:
            self.session.delete_card(card_data)

handler_types = {
    'issue': IssueHandler,
    'project': ProjectHandler,
}
