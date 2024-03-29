import os
from utils import clients
from looker_sdk.sdk.api40 import models
import sys


def get_project_repo_url(project_id: str, sdk: any) -> str:
    pass


def get_models(project_id: str, sdk: any):
    # TODO: Need to reserch name vs ID for projects
    models = sdk.all_lookml_models()
    # project_models = [ (m.name, m.project_name, m.explores) for m in models if m.project_name == project_name ]
    return [m.name for m in models if m.project_name == project_id]


def copy_folder(folder_name: str, folder_id: int, source: str, destination: str):
    ### Copy folder and User Defined Dashboards

    if not folder_name and not folder_id:
        raise ValueError("folder_name or folder_id required")

    # if folder_name passed, check for duplicate folder names
    # if 2+ found, exit with warning to use folder_id
    sdk_source = clients.get_looker_sdk(source)
    sdk_destination = clients.get_looker_sdk(destination)

    if folder_name:
        # folders_all_source = sdk_source.all_folders()
        folders_all_source = sdk_source.search_folders(name=folder_name)

        # We may have multiple folders with the same name.
        folder_ids = [f.id for f in folders_all_source if f.name == folder_name]

        if not folder_ids:
            print(f"No matching folder found with that name at {source}.")
            sys.exit(1)
        elif len(folder_ids) > 1:
            print(f"More than one matching folder found with that name at {source}, please use --folder_id")
            sys.exit(1)    

        # check destination for existing folder with same name, if name passed
        folders_all_destination = sdk_destination.all_folders()
        # using all_folders instead of search_folders as we need all_folders to find the parent shared folder
        # folders_all_destination = sdk_destination.search_folders(name=folder_name)

        # Find Shared folder ID, which is almost always 1
        shared_folder_id_destination = \
            [f.id for f in folders_all_destination if f.name == "Shared" and f.parent_id is None][0]

        if shared_folder_id_destination is None:
            print("Shared folder not found at destination.")
            sys.exit(1)

        # Find folder at destination under Shared folder
        folder_ids_destination = \
            [f.id for f in folders_all_destination if f.name == folder_name
             and f.parent_id == shared_folder_id_destination]

        destination_folder_id = None

        # TODO: If --force, etc, get folder ID at destination and copy to it?
        folders_destination_exists = None
        if folder_ids_destination:
            print(f"Folder {folder_name} already exists at {destination}, copying into it.")
            folders_destination_exists = True
            destination_folder_id = folder_ids_destination[0]
            # sys.exit(1)
        else:
            folders_destination_exists = False

    folder_id_to_copy = folder_id or folder_ids[0]

    # if id passed, we will need name to use when creating at destination
    if folder_id and not folder_name:
        folder_name = sdk_source.folder(folder_id_to_copy).name
        print(f"Folder name: {folder_name}")

    print(
        f"Copying folder: {folder_name} (id: {folder_id_to_copy}) and user defined dashboards from {source} to {destination}")

    # create folder at destination if needed, putting under Sharded #TODO

    if not folders_destination_exists:
        try:
            create_folder_result = sdk_destination.create_folder(
                body=models.CreateFolder(name=folder_name, parent_id=shared_folder_id_destination))

            destination_folder_id = create_folder_result.id
            print(f"Created folder at destination: {folder_name} (id: {destination_folder_id})")

        except Exception as e:
            print("Folder Creation at Destination Failed")
            print(e)

    # get all user defined dashboards in folder at source
    dashboards_all_source = sdk_source.folder_dashboards(folder_id=folder_id_to_copy, fields="id")
    print(f"Found {len(dashboards_all_source)} dashboards in folder {folder_name} at {source}, copying...")

    for dashboard in dashboards_all_source:
        print(f"Copying dashboard id: {dashboard.id}")

        # Convert UDD to LookML
        resp_db_lookml = sdk_source.dashboard_lookml(dashboard_id=dashboard.id)

        db_lookml_id = resp_db_lookml.dashboard_id
        db_lookml: str = resp_db_lookml.lookml

        print(f"Dashboard LookML, ID: {db_lookml_id}")
        # print(f"Dashboard len(LookML): {len(db_lookml)}")
        print(f"Destination Folder ID: {destination_folder_id}")

        # Reconstitute LoomML DB to UDD at destination

        try: 
            response = sdk_destination.import_dashboard_from_lookml(
                body=models.WriteDashboardLookml(
                    folder_id=destination_folder_id,
                    lookml=db_lookml
                ))
            print("Dashboard Copied")
        except Exception as e:
            if type(e).__name__ == "SDKError":
                print("!!! SDK Error: make sure a copy of dashboard: is not in the trash folder at the destination.")
            else:
                raise e
        

def copy_project(project_id, source, destination, env_github_org, branch_name, project_name):
    print(f"Copying project {project_id}")
    print(f"source: {source}  --> destination: {destination}")

    # sdk reference for source and destination instances
    sdk_source = clients.get_looker_sdk(source)
    sdk_destination = clients.get_looker_sdk(destination)

    # check source project ID or get source project id if name passed.
    if project_id:
        # project: models.Project = sdk_source.project(project_id=project_id, fields="id, git_remote_url, uses_git")
        project: models.Project = sdk_source.project(project_id=project_id)
        if project.id != project_id:
            raise Exception('Project Match Err')
    else:
        raise Exception('Missing Project ID')
        # # find project_id by name
        # all_projects = sdk_source.all_projects(fields="id, git_remote_url, uses_git")
        # print("all projects: ")

    # Check if project_id exists on projection, if so, warn and stop unless --force was used?

    # Check if project exists at destination
    # if project_id not in [p.name for p in sdk_destination.all_projects()]:
    if project_id not in [p.id for p in sdk_destination.all_projects()]:
        # Todo: Slow, maybe try catch project() check?
        print(f"*** Creating Project {project_id}.")
        # Create project on Production
        response = sdk_destination.create_project(
            models.Project(name=project_id)
        )
    else:
        print(f"*** Project {project_id} exists.\n")
        # raise Exception(f"Project {project_id} already exists on production.")

    # Update to dev mode
    print("Update to Develop Mode\n")
    response = sdk_destination.update_session(
        body=models.WriteApiSession(workspace_id="dev")
    )

    # Setup repo
    source_project = sdk_source.project(project_id)
    # source_project_repo_url = \
    github_repo_url = source_project.git_remote_url
    github_production_branch_name = source_project.git_production_branch_name
    # github_client = clients.get_github_client()
    gitrepo_client = clients.get_repo_client()

    active_git_branch_dev = sdk_source.git_branch(project_id).name
    print(f"Active Git Branch: {active_git_branch_dev}")

    # User user provided branch, otherwise active_git_branch_dev
    target_branch = branch_name or active_git_branch_dev
    print(f"Target Branch: {target_branch}")

    if not os.environ['REPO_BRAND'] or os.environ['REPO_BRAND'] == 'github':
        try:
            org = gitrepo_client.get_organization(env_github_org or os.environ['GITHUB_ORG'])
        except Exception as e:
            print(f"Issue using Github Organization: {env_github_org or os.environ['GITHUB_ORG']}")
            sys.exit(1)
    else:
        # TODO (Maybe forgo Org for GitLab?)
        org = None  

    print(f"GitHub Organization: {org}")
    github_service_name = source_project.git_service_name

    # For remote repositories
    repo_name = github_repo_url.split('.git')[0].split('/')[-1]

    print(f"repo_name: {repo_name}")
    print(f"github_repo_url: {github_repo_url}")
    print(f"github_production_branch_name: {github_production_branch_name}")
    print(f"github_org: {org}")

    # Update Project at Destination Instance
    # Set Advance deploy mode, TODO: Read previous state and return to it at end of run
    # TODO: *****
    print("Updating to Advance deploy mode\n")
    response = sdk_destination.update_project(
        project_id=project_id,
        body=models.WriteProject(git_release_mgmt_enabled=True)
    )

    # Check for existence of production branch in repo, create if needed
    # TODO: Should always be here, error if not, do not create
    print(f"Checking repo: {repo_name}")

    
    repo = None  # GitHub
    project = None  # GitLab

    # Default to Github unless GitLab is specified
    if not os.environ['REPO_BRAND'] or os.environ['REPO_BRAND'] == 'github':
        if repo_name not in [r.name for r in org.get_repos()]:
            raise ValueError(f"Repo {repo_name} does not exit.... verify the correct Github Organization is set")
    else: 
        projects = gitrepo_client.projects.list(iterator=True, search=repo_name)

        # Search on exact name should return exactly one hit
        if projects.total > 1 or projects.total == 0:
            raise ValueError(f"Repo {repo_name} does not exit.... verify the correct GitLab Organization is set")
        
        for project in projects:  
            # list comprehension is not working as not true iterator
            # expect only 1 by this point
            if project.name.lower() != repo_name.lower():
                raise ValueError(f"Repo {repo_name} does not exit.... verify the correct GitLab Organization is set")

    # Todo 
    if not os.environ['REPO_BRAND'] or os.environ['REPO_BRAND'] == 'github':
        repo = org.get_repo(repo_name)
        print(f"Repo: {repo.name}")
    else: 
        print(f"GitLab Project {project.name}") 

    # set up Github deploy key
    try:
        # get existing deploy key from Looker, if it exists
        print("Get deploy key.")
        # deploy_key = sdk_production.git_deploy_key(
        #     project_name).split(' Looker')[0]
        deploy_key = sdk_destination.git_deploy_key(project_id).split('Looker')[0].strip()
        # ''.join(deploy_key.split(' ')[0:2])  # remove suffix?

        # if not already linked to Github repo, link it

        if not os.environ['REPO_BRAND'] or os.environ['REPO_BRAND'] == 'github':
        # TODO, does not seem to find exiting keys
            if deploy_key not in [k.key for k in repo.get_keys()]:
                repo.create_key(key=deploy_key, title='Looker', read_only=False)
        else:
            keys = project.keys.list()
            key_exists = False
            for key in keys:  
                if deploy_key == key.key:
                    print(f"Deploy key already exists in GitLab project {project.name}")
                    key_exists = True
                    break
            
            if not key_exists:
                # Create Key GitLab 
                # repo.create_key(key=deploy_key, title='Looker', read_only=False)
                pass
            
    except Exception as e:
        # this might fail if there is no key in Looker yet
        # or if the key has already been linked to a different repo

        # create a new deploy key in Looker and link to Github
        print("Deploy key not found, creating new one.")
        if not os.environ['REPO_BRAND'] or os.environ['REPO_BRAND'] == 'github':
            deploy_key = sdk_destination.create_git_deploy_key(project_id)
            # print(f"deploy Key: {deploy_key}")
            repo.create_key(key=deploy_key, title='Looker', read_only=False)
        else:
            deploy_key = sdk_destination.create_git_deploy_key(project_id)
            key = project.keys.create({'title': 'Looker', 'key': deploy_key})
            

            
    # Update project with Repo URL
    response = sdk_destination.update_project(
        project_id,
        models.WriteProject(name=project_id,
                            git_remote_url=github_repo_url, git_service_name=github_service_name)
    )

    # # Create deploy branch
    # # Check for test_branch, create if needed:
    # # response = sdk_production.create_git_branch(project_name, body=WriteGitBranch(name='test_branch'))
    # # print(response)

    # response = sdk_production.all_git_branches(project_name)
    # active_git_branch_dev = sdk_production.git_branch(project_name)

    # print(f"active_git_branch_dev: {active_git_branch_dev}")

    # Call SDK.update_lookml_model for each model for the project.

    models_destination = get_models(project_id, sdk_destination)
    models_source = get_models(project_id, sdk_source)

    print(f"models_source: {models_source}")

    for model in models_source:
        if model not in models_destination:
            print(f"model {model} not in production, creating...")

            response = sdk_destination.create_lookml_model(
                body=models.WriteLookmlModel(
                    name=model,
                    project_name=project_id,
                    unlimited_db_connections=True
                ))

            print(f"create_lookml_model: {model}")

        else:
            print(f"model {model} exists in production")

            response = sdk_destination.update_lookml_model(
                lookml_model_name=model,
                body=models.WriteLookmlModel(
                    name=model,
                    project_name=project_id
                ))

            print(f"update_lookml_model: {model}")

    # TODO: Required for the new project
    try:

        # response = sdk_destination.deploy_ref_to_production(
        #     project_id, github_production_branch_name) or None
        # print(response)

        response = sdk_destination.update_git_branch(
            project_id=project_id,
            body=models.WriteGitBranch(
                name=target_branch
            ))

        print(response)

        # response = sdk_destination.reset_project_to_remote(project_id=project_id)
        # print(response)

        # response = sdk_destination.update_git_branch(
        #     project_id=project_id,
        #     body=models.WriteGitBranch(
        #     name=github_production_branch_name
        # ))
        # print(response)

    except Exception as err:
        print(f"Error deploying code: {target_branch} to project: {project_id}")
        print(f"{err}")

    # Switch back from dev to production mode
    print("Switching back to production mode.")
    response = sdk_destination.update_session(
        body=models.WriteApiSession(workspace_id="production")
    )
    # print(response)

    # # Set Advance deploy mode off?  This is on by default.
    # # print("Switch off Advance deploy mode\n")
    # # response = sdk_production.update_project(
    # #     project_id=project_name,
    # #     body=WriteProject(git_release_mgmt_enabled=False)
    # # )
    # # print(response)
