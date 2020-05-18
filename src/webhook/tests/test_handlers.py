from unittest import mock

from django.test import TestCase

from webhook import handlers

from webhook.tests.utils import get_project_webhook_data

from_on_deck_project_data = {
    "action": "moved",
    "changes": {"column_id": {"from": 2001377}},
    "project_card": {
        "url": "https://api.github.com/projects/columns/cards/6731956",
        "column_url": "https://api.github.com/projects/columns/2001376",
        "column_id": 2001376,
        "id": 6731956,
        "note": None,
        "creator": {
            "login": "rca",
            "id": 53537,
            "avatar_url": "https://avatars3.githubusercontent.com/u/53537?v=4",
            "gravatar_id": "",
            "url": "https://api.github.com/users/rca",
            "html_url": "https://github.com/rca",
            "followers_url": "https://api.github.com/users/rca/followers",
            "following_url": "https://api.github.com/users/rca/following{/other_user}",
            "gists_url": "https://api.github.com/users/rca/gists{/gist_id}",
            "starred_url": "https://api.github.com/users/rca/starred{/owner}{/repo}",
            "subscriptions_url": "https://api.github.com/users/rca/subscriptions",
            "organizations_url": "https://api.github.com/users/rca/orgs",
            "repos_url": "https://api.github.com/users/rca/repos",
            "events_url": "https://api.github.com/users/rca/events{/privacy}",
            "received_events_url": "https://api.github.com/users/rca/received_events",
            "type": "User",
            "site_admin": False,
        },
        "created_at": "2018-01-16T17:49:17Z",
        "updated_at": "2018-01-17T19:59:50Z",
        "content_url": "https://api.github.com/repos/openslate/openslate/issues/468",
        "after_id": None,
    },
    "organization": {
        "login": "openslate",
        "id": 1767240,
        "url": "https://api.github.com/orgs/openslate",
        "repos_url": "https://api.github.com/orgs/openslate/repos",
        "events_url": "https://api.github.com/orgs/openslate/events",
        "hooks_url": "https://api.github.com/orgs/openslate/hooks",
        "issues_url": "https://api.github.com/orgs/openslate/issues",
        "members_url": "https://api.github.com/orgs/openslate/members{/member}",
        "public_members_url": "https://api.github.com/orgs/openslate/public_members{/member}",
        "avatar_url": "https://avatars2.githubusercontent.com/u/1767240?v=4",
        "description": "",
    },
    "sender": {
        "login": "rca",
        "id": 53537,
        "avatar_url": "https://avatars3.githubusercontent.com/u/53537?v=4",
        "gravatar_id": "",
        "url": "https://api.github.com/users/rca",
        "html_url": "https://github.com/rca",
        "followers_url": "https://api.github.com/users/rca/followers",
        "following_url": "https://api.github.com/users/rca/following{/other_user}",
        "gists_url": "https://api.github.com/users/rca/gists{/gist_id}",
        "starred_url": "https://api.github.com/users/rca/starred{/owner}{/repo}",
        "subscriptions_url": "https://api.github.com/users/rca/subscriptions",
        "organizations_url": "https://api.github.com/users/rca/orgs",
        "repos_url": "https://api.github.com/users/rca/repos",
        "events_url": "https://api.github.com/users/rca/events{/privacy}",
        "received_events_url": "https://api.github.com/users/rca/received_events",
        "type": "User",
        "site_admin": False,
    },
}

to_on_deck_project_data = {
    "action": "moved",
    "changes": {"column_id": {"from": 2001376}},
    "project_card": {
        "url": "https://api.github.com/projects/columns/cards/6731956",
        "column_url": "https://api.github.com/projects/columns/2001377",
        "column_id": 2001377,
        "id": 6731956,
        "note": None,
        "creator": {
            "login": "rca",
            "id": 53537,
            "avatar_url": "https://avatars3.githubusercontent.com/u/53537?v=4",
            "gravatar_id": "",
            "url": "https://api.github.com/users/rca",
            "html_url": "https://github.com/rca",
            "followers_url": "https://api.github.com/users/rca/followers",
            "following_url": "https://api.github.com/users/rca/following{/other_user}",
            "gists_url": "https://api.github.com/users/rca/gists{/gist_id}",
            "starred_url": "https://api.github.com/users/rca/starred{/owner}{/repo}",
            "subscriptions_url": "https://api.github.com/users/rca/subscriptions",
            "organizations_url": "https://api.github.com/users/rca/orgs",
            "repos_url": "https://api.github.com/users/rca/repos",
            "events_url": "https://api.github.com/users/rca/events{/privacy}",
            "received_events_url": "https://api.github.com/users/rca/received_events",
            "type": "User",
            "site_admin": False,
        },
        "created_at": "2018-01-16T17:49:17Z",
        "updated_at": "2018-01-17T19:26:28Z",
        "content_url": "https://api.github.com/repos/openslate/openslate/issues/468",
        "after_id": None,
    },
    "organization": {
        "login": "openslate",
        "id": 1767240,
        "url": "https://api.github.com/orgs/openslate",
        "repos_url": "https://api.github.com/orgs/openslate/repos",
        "events_url": "https://api.github.com/orgs/openslate/events",
        "hooks_url": "https://api.github.com/orgs/openslate/hooks",
        "issues_url": "https://api.github.com/orgs/openslate/issues",
        "members_url": "https://api.github.com/orgs/openslate/members{/member}",
        "public_members_url": "https://api.github.com/orgs/openslate/public_members{/member}",
        "avatar_url": "https://avatars2.githubusercontent.com/u/1767240?v=4",
        "description": "",
    },
    "sender": {
        "login": "rca",
        "id": 53537,
        "avatar_url": "https://avatars3.githubusercontent.com/u/53537?v=4",
        "gravatar_id": "",
        "url": "https://api.github.com/users/rca",
        "html_url": "https://github.com/rca",
        "followers_url": "https://api.github.com/users/rca/followers",
        "following_url": "https://api.github.com/users/rca/following{/other_user}",
        "gists_url": "https://api.github.com/users/rca/gists{/gist_id}",
        "starred_url": "https://api.github.com/users/rca/starred{/owner}{/repo}",
        "subscriptions_url": "https://api.github.com/users/rca/subscriptions",
        "organizations_url": "https://api.github.com/users/rca/orgs",
        "repos_url": "https://api.github.com/users/rca/repos",
        "events_url": "https://api.github.com/users/rca/events{/privacy}",
        "received_events_url": "https://api.github.com/users/rca/received_events",
        "type": "User",
        "site_admin": False,
    },
}

on_deck_column_data = {
    "url": "https://api.github.com/projects/columns/2001377",
    "project_url": "https://api.github.com/projects/1206552",
    "cards_url": "https://api.github.com/projects/columns/2001377/cards",
    "id": 2001377,
    "name": "On Deck",
    "created_at": "2018-01-11T19:36:33Z",
    "updated_at": "2018-01-17T19:26:28Z",
}


class ProjectHandlerTestCase(TestCase):
    def _get_project_handler(self, data):
        project_handler = handlers.ProjectHandler(data)
        project_handler.session = mock.Mock()

        return project_handler

    def test_move_grooming_card(self):
        data = get_project_webhook_data()
        project_handler = self._get_project_handler(data)

        project_handler.session.request.return_value.json.return_value = {
            "url": "https://api.github.com/projects/columns/2001376",
            "project_url": "https://api.github.com/projects/1206552",
            "cards_url": "https://api.github.com/projects/columns/2001376/cards",
            "id": 2001376,
            "name": "Grooming",
            "created_at": "2018-01-11T19:36:33Z",
            "updated_at": "2018-01-17T17:46:36Z",
        }

        project_handler.sync_on_deck = mock.Mock()

        project_handler.run()

        # a grooming card will not sync on deck
        project_handler.sync_on_deck.assert_not_called()

    def test_move_on_deck_card(self):
        data = get_project_webhook_data()
        project_handler = self._get_project_handler(data)

        project_handler.session.request.return_value.json.return_value = {
            "url": "https://api.github.com/projects/columns/2001376",
            "project_url": "https://api.github.com/projects/1206552",
            "cards_url": "https://api.github.com/projects/columns/2001376/cards",
            "id": 2001376,
            "name": "On Deck",
            "created_at": "2018-01-11T19:36:33Z",
            "updated_at": "2018-01-17T17:46:36Z",
        }

        project_handler.run()

        # an on deck card will sync!
        project_handler.sync_on_deck.assert_called_with()

    def test_detect_remove_from_on_deck(self):
        project_handler = self._get_project_handler(from_on_deck_project_data)
        project_handler.remove_from_on_deck = mock.Mock()

        project_handler.run()

        project_handler.remove_from_on_deck.assert_called_with(mock.ANY)

    def test_detect_add_to_on_deck(self):
        project_handler = self._get_project_handler(to_on_deck_project_data)
        project_handler.add_to_on_deck = mock.Mock()

        project_handler.run()

        project_handler.add_to_on_deck.assert_called_with(mock.ANY)

    def test_add_to_on_deck(self):
        project_handler = self._get_project_handler(to_on_deck_project_data)
        project_handler.add_to_on_deck = mock.Mock()

        project_handler.run()

        project_handler.add_to_on_deck.assert_called_with(mock.ANY)
