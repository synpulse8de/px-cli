import os

from copier import run_copy, run_update

from pulse8_core_cli.environment.functions import ENV_GITHUB_USER


def backend_create(answers_file: str, defaults: bool, skip_answered: bool):
    print('Starting project creation from template...')

    try:
        github_user = os.environ[ENV_GITHUB_USER]
    except KeyError:
        print("Error: GITHUB_USER environment variable is not set")
        exit(1)

    print(f'Creating project for github user {github_user}')

    worker = run_copy(f'https://{github_user}@github.com/synpulse-group/pulse8-core-backend-template.git',
                      '.', unsafe=True, defaults=defaults, answers_file=answers_file, skip_answered=skip_answered)

    project_id = worker.answers.user.get('project_id')

    os.system('git init')
    os.system('git add .')
    os.system('git commit -m "[PULSE8] Generated using Pulse8 Core Template" --quiet')
    os.system('git branch -M main')

    print(f'Creating repository {project_id}')

    os.system(f'gh repo create {project_id} --private --source=. --remote=upstream')
    os.system(f'git remote add origin https://github.com/{github_user}/{project_id}.git')
    os.system('git push -u origin main')

    print('Pushed generated project to newly created private repository. Happy coding!')


def backend_update(answers_file: str, defaults: bool, skip_answered: bool):
    print('Pulling latest template data...')

    run_update('.', overwrite=True, unsafe=True, defaults=defaults,
               answers_file=answers_file, skip_answered=skip_answered)
