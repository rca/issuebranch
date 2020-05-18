from unittest import TestCase, mock

from issuebranch import utils


class UtilsTestCase(TestCase):
    def test_get_issue_number_from_card_data(self, *mocks):
        """
        Ensures an issue number is returned
        """
        card_data = {
            "url": "https://api.github.com/projects/columns/cards/xxxxxx",
            "project_url": "https://api.github.com/projects/xxxxxxx",
            "creator": {"login": "marcusianlevine", "lots_of_other_keys": "removed"},
            "created_at": "2019-02-21T14:58:04Z",
            "updated_at": "2019-02-27T21:42:04Z",
            "column_url": "https://api.github.com/projects/columns/xxxxxxx",
            "content_url": "https://api.github.com/repos/org/repo/issues/1234",
        }

        issue_number = utils.get_issue_number_from_card_data(card_data)

        self.assertEqual(1234, issue_number)

    def test_get_label(self, *mocks):
        """
        Ensures the label is properly parsed
        """
        self.assertEqual(
            "team_core_engineering", utils.get_label("TEAM - Core Engineering")
        )

    def test_get_label_with_prefix(self, *mocks):
        """
        Ensures the label is properly parsed
        """
        self.assertEqual(
            "team:core_engineering",
            utils.get_label("TEAM - Core Engineering", prefix="team"),
        )
