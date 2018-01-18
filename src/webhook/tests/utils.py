org = {
    'login': 'openslate',
    'id': 1767240,
    'url': 'https://api.github.com/orgs/openslate',
    'repos_url': 'https://api.github.com/orgs/openslate/repos',
    'events_url': 'https://api.github.com/orgs/openslate/events',
    'hooks_url': 'https://api.github.com/orgs/openslate/hooks',
    'issues_url': 'https://api.github.com/orgs/openslate/issues',
    'members_url': 'https://api.github.com/orgs/openslate/members{/member}',
    'public_members_url': 'https://api.github.com/orgs/openslate/public_members{/member}',
    'avatar_url': 'https://avatars2.githubusercontent.com/u/1767240?v=4',
    'description': ''
}

user = {
    'login': 'rca',
    'id': 53537,
    'avatar_url': 'https://avatars3.githubusercontent.com/u/53537?v=4',
    'gravatar_id': '',
    'url': 'https://api.github.com/users/rca',
    'html_url': 'https://github.com/rca',
    'followers_url': 'https://api.github.com/users/rca/followers',
    'following_url': 'https://api.github.com/users/rca/following{/other_user}',
    'gists_url': 'https://api.github.com/users/rca/gists{/gist_id}',
    'starred_url': 'https://api.github.com/users/rca/starred{/owner}{/repo}',
    'subscriptions_url': 'https://api.github.com/users/rca/subscriptions',
    'organizations_url': 'https://api.github.com/users/rca/orgs',
    'repos_url': 'https://api.github.com/users/rca/repos',
    'events_url': 'https://api.github.com/users/rca/events{/privacy}',
    'received_events_url': 'https://api.github.com/users/rca/received_events',
    'type': 'User',
    'site_admin': False
}


def get_project_webhook_data():
    return {
        'action': 'moved',
        'changes': {
            'column_id': {'from': 2001375}
        },
        'project_card': {
            'url': 'https://api.github.com/projects/columns/cards/6731956',
            'column_url': 'https://api.github.com/projects/columns/2001376',
            'column_id': 2001376,
            'id': 6731956,
            'note': None,
            'creator': user.copy(),
            'created_at': '2018-01-16T17:49:17Z',
            'updated_at': '2018-01-17T17:46:36Z',
            'content_url': 'https://api.github.com/repos/openslate/openslate/issues/468',
            'after_id': None
        },
        'organization': org.copy(),
        'sender': user.copy()
    }
