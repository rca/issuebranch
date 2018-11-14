import shlex

import sh


def run_command(command, **kwargs):
    """
    Runs the command using sh

    Args:
        command (str): The command to run

    Returns:
        the executed sh process
    """
    command_l = shlex.split(command)

    return getattr(sh, command_l[0])(*command_l[1:], **kwargs)
