def get_action_type(webhook_data):
    action_type = None

    if 'issue' in webhook_data:
        return 'issue'

    if webhook_data.get('action') == 'moved':
        if webhook_data.get('project_card'):
            return 'project'

    return action_type
