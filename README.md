# Looker Project Utility : lproject

## Usage: 
#### Copy Project
```
lproject copy {project_name}
```
#### Copy folder and User Defined Dashboards
```
lproject copy --folder_name={name of folder}
```
#### Combined Project and Folder with UD Dashboards
```
lproject copy {project_name} --folder_name={name of folder}
```

This is use a source and destination instance as defined by [Source] and [Destination] in the looker.ini config file by default. 
It will also use the default GitHub API Token and GitHub Organization as defined by GITHUB_API_TOKEN and GITHUB_ORG in the .env file.

### Flags
```
--project_id    : The ID of the project to copy, optinoal if id passed after copy command

--source        : The source Looker instance to copy from as labled in the looker.ini config file.
--destination   : The destination Looker instance to copy from as labled in the looker.ini config file.

--folder_name   : The folder name to copy.  (It must be unique)

i.e. lproject copy --project_id=customer_progect --source=Development --destination=Production 
```

### Future Enhancements: 
-- branch = "main" | "master", unless passed through --branch flag
-- Add --folder_id when name is not unique
-- Chose specifc source repo branch / tag to copy 
-- Change project ID / Name at destination 
-- force (overwrite destination project)

## Installation 

### Option 1:
 Clone this repo, run: 

```pip3 install -r requirements.txt```

### Option 2: (future)
Copy the whl file from /dist/LookerProjectUtility*.whl to a local directory.

```pip3 install -m Looker``` 


## Configuration Files 
### looker.ini 
#### Label names are arbitrary but [Source] and [Destination] will be used as defaults if included.
```
[Source]
base_url=https:// 
client_id= 
client_secret= 
verify_ssl=True

[Destination]
base_url=https:// 
client_id= 
client_secret=
verify_ssl=True
```

### .env
```
# Swich to set current Repo brand
REPO_BRAND=     # github | gitlab  (optional if github)

# GitHub
GITHUB_API_TOKEN= {token}
GITHUB_ORG= {GitHub Organization}

# GitLab 
GITLAB_API_TOKEN=


```

### Dependencies (partial)
python-gitlab==3.9.0
https://python-gitlab.readthedocs.io/en/stable/gl_objects/deploy_keys.html

PyGithub==1.55
https://github.com/PyGithub/PyGithub

