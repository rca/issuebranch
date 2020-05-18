from unittest import TestCase
from unittest.mock import Mock

from issuebranch.backends.github import GithubLinkHeader

LINK_HEADER = (
    '<https://api.github.com/projects/columns/1255924/cards?page=2>; rel="next", '
    '<https://api.github.com/projects/columns/1255924/cards?page=4>; rel="last"'
)


class GithubLinkHeaderTestCase(TestCase):
    def test_parse(self):
        parsed = GithubLinkHeader.parse(LINK_HEADER)

        self.assertEqual(2, len(parsed))

        link = parsed[0]

        self.assertEqual(GithubLinkHeader, type(link))

        self.assertEqual(
            "https://api.github.com/projects/columns/1255924/cards?page=2", link.url
        )
        self.assertEqual("next", link.rel)
