import re

from issuebranch.backends.github import GithubSession


LABEL_RE = re.compile(r'[^0-9a-z ]', flags=re.IGNORECASE)


def get_issue_number_from_card_data(card_data: dict) -> int:
    """
    Returns the issue number from the given card data

    Can be None if the card is a note or some other non-issue card

    Args:
        card_data: the card data returned by the GH API

    Returns:
        Issue number or None
    """
    content_url = card_data.get('content_url')
    if not content_url:
        return

    issue_number = content_url.rsplit('/', 1)[-1]

    return int(issue_number)


def get_label(buf: str, prefix: str = None) -> str:
    """
    Returns a label

    For example, the string 'TEAM - Core Engineering' should return 'team:core_engineering'

    Args:
        buf: the original string
        prefix: a label prefix if the label should have one

    Returns:
        str
    """
    lower_buf = LABEL_RE.sub('', buf).lower()
    lower_buf_split = lower_buf.split()

    if prefix:
        # remove the first element if it is the prefix
        if lower_buf_split[0] == prefix:
            lower_buf_split.pop(0)

    underscored = '_'.join(lower_buf_split)

    label = underscored
    if prefix:
        label = f'{prefix}:{label}'

    return label


def label_milestone_issues():
    """
    Labels all issues in a milestone with that milestone's respective label
    """
    session = GithubSession()

    labels = list(session.get_labels())
    labels_by_name = dict([(x['name'], x) for x in labels])

    milestones = list(session.get_milestones())

    for milestone in milestones:
        label_data = labels_by_name[f'epic:{milestone["title"].strip()}']

        for issue in session.get_issues(milestone=milestone["number"], state='all'):
            session.add_label(label_data, number=issue['number'])


def milestone_labels(argv=None):
    """
    creates labels out of milestones
    """
    argv = argv or sys.argv[1:]

    parser = argparse.ArgumentParser()

    parser.add_argument('color', help='color to make the labels')

    args = parser.parse_args(argv)

    session = GithubSession()

    labels = session.get_labels()

    labels_by_name = dict([(label['name'], label) for label in labels])

    for milestone in session.get_milestones():
        label_name = f'epic:{milestone["title"]}'

        if label_name in labels_by_name:
            continue

        labels_by_name[label_name] = session.create_label(label_name, args.color)

    return labels_by_name
