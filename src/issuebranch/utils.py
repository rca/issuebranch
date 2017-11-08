from issuebranch.backends.github import GithubSession


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
