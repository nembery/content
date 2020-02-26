import demistomock as demisto
from CommonServerPython import *  # noqa: E402 lgtm [py/polluting-import]
from CommonServerUserPython import *  # noqa: E402 lgtm [py/polluting-import]
# IMPORTS

import requests
from skilletlib import SkilletLoader
from skilletlib.skillet.base import Skillet

# Disable insecure warnings
requests.packages.urllib3.disable_warnings()

# CONSTANTS
DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


class Client:

    repo = ''
    branch = ''
    skillets = list()

    skilletLoader = None

    def __init__(self, repo: str, branch: str, instance: str):
        self.repo = repo
        self.branch = branch

        self.instance = instance
        LOG(instance)
        self.skilletLoader = SkilletLoader()
        self.skillets = self.skilletLoader.load_from_git(repo, instance, branch, local_dir='.')

    def list_skillets(self) -> list:
        return self.skillets

    def get_skillet(self, name) -> Skillet:
        return self.skilletLoader.get_skillet_with_name(name)


def test_module(client):
    """
    Returning 'ok' indicates that the integration works like it is supposed to. Connection to the service is successful.

    Args:
        client: HelloWorld client

    Returns:
        'ok' if test passed, anything else will fail the test.
    """

    return 'ok'


def execute_validation_command(client, args):

    skillet_id = args.get('skillet_id')
    ip_address = args.get('ip_address')
    username = args.get('username')
    password = args.get('password')

    context = dict()
    context['ip_address'] = ip_address
    context['username'] = username
    context['password'] = password

    skillet = client.get_skillet(skillet_id)
    skillet.initialize_context(context)

    results = skillet.execute(context)

    if skillet.type == 'pan_validation':

        readable_output = f'## Execution Results\n\n'
        readable_output += 'Test  |  Description  |  Result  | Severity  |  More Information\n'
        readable_output += '---  | ---  | ---  | --- | --- \n'

        validation_results = results.get('pan_validation', {})
        output = dict()

        for k, v in validation_results.items():
            res = v.get('results', 'False')
            link = v.get('documentation_link', '')
            label = v.get('label', '')
            severity = v.get('severity', 'low')
            readable_output += f'{k}|{label}|{res}|{severity}|{link}\n'
            output[k] = res
    else:
        # FIXME - handle panos output here
        readable_output = f'## Execution Results'
        readable_output += f'{results}'
        output = results

    return (
        readable_output,
        output,
        'raw response here'  # raw response - the original response
    )


def list_skillets_command(client, args):
    skillets = client.list_skillets()
    readable_output = f'## Available Skillets\n\n'
    outputs = dict()
    for s in skillets:
        readable_output += f'* {s.name} - {s.label}\n'
        outputs[s.name] = s.label

    return (
        readable_output,
        outputs,
        'raw response here'  # raw response - the original response
    )


def main():
    """
        PARSE AND VALIDATE INTEGRATION PARAMS
    """
    repo = demisto.params().get('repo')
    branch = demisto.params().get('branch')

    LOG(f'Command being called is {demisto.command()}')
    try:

        instance = demisto.integrationInstance()

        client = Client(
            repo=repo,
            branch=branch,
            instance=instance)

        if demisto.command() == 'test-module':
            # This is the call made when pressing the integration Test button.
            result = test_module(client)
            demisto.results(result)

        elif demisto.command() == 'pan-os-skilletlib-list':
            return_outputs(*list_skillets_command(client, demisto.args()))

        elif demisto.command() == 'pan-os-skilletlib-validate':
            return_outputs(*execute_validation_command(client, demisto.args()))

    # Log exceptions
    except Exception as e:
        return_error(f'Failed to execute {demisto.command()} command. Error: {str(e)}')


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
