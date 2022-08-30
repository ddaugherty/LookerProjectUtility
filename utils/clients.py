import os
from urllib3.util import Retry
import looker_sdk
from looker_sdk.sdk.api40.models import WriteApiSession
from dotenv import load_dotenv
from github import Github


def get_github_credentials():
    # Load credentials from .env file
    
    load_dotenv()
    try:
        if not os.environ['GITHUB_API_TOKEN']:
            raise ValueError("GITHUB_API_TOKEN environment variable not set")
        return os.environ['GITHUB_API_TOKEN']
    except KeyError as e:
        raise KeyError("clients.py: environment variable not set, see documentation re: .env file") from e

def get_gitlab_credentials():
    # Load credentials from .env file
    
    load_dotenv()
    try:
        if not os.environ['GITLAB_API_TOKEN']:
            raise ValueError("GITLAB_API_TOKEN environment variable not set")
        return os.environ['GITLAB_API_TOKEN']
    except KeyError as e:
        raise KeyError("clients.py: environment variable not set, see documentation re: .env file") from e


def get_repo_credentials():
    # Get credentials from .env file
    # Added to support GitLab as well as GitHub

    load_dotenv()
    
    # Defualt to GitHub unless otherwise specified
    if not os.environ['REPO_BRAND'] or os.environ['REPO_BRAND'] == 'github':
        get_github_credentials()
    
    if os.environ['REPO_BRAND'] == 'gitlab':
        get_gitlab_credentials()


def get_github_client():
    github_credentials = get_github_credentials()
    return Github(
        github_credentials.strip(),
        retry=Retry(total=10, status_forcelist=(500, 502, 504), backoff_factor=0.3))


def get_looker_sdk(section='looker') -> any:
    # Pass second for source or destination for specific instance as defined in  looker.ini
    looker_ini_path = 'looker.ini'
    sdk = looker_sdk.init40(config_file=looker_ini_path, section=section)  # relies on looker.ini being set up
    sdk.update_session(WriteApiSession(workspace_id='dev'))  # turn on dev-mode -- required for create_project
    return sdk
