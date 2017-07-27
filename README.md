# Issue branches

Create branches based off issue number and title


## Setup

You'll need to set the following environment variables for the command to work.


### ISSUE_BACKEND

Can be set to `github` or `redmine` (specifically plan.io)


### ISSUE_BACKEND_API_KEY

Your account's API key.  On Github this is a [Personal Access Token](https://github.com/settings/tokens).


### ISSUE_BACKEND_USER

For github, the user or organization the issue repository is under.


### ISSUE_BACKEND_REPO

The organization or user's repo to find the issues.


The above environment variables will make a request similar to the following:

```
curl -H "Authorization token ${ISSUE_BACKEND_API_KEY}" https://api.github.com/repos/${ISSUE_BACKEND_USER}/${ISSUE_BACKEND_REPO}/issues/${issue_number}
```


## changetype labels

![Issue Example](images/refactor-endpoints.png?raw=true)


The command expects to find a label prefixed with `changetype:` to create the branch.  For example, some labels can be `changetype:feature`, `changetype:bugfix`, etc.  This prefix will be used to namespace the branch.


## Basic Usage

The example below issue 54 is labeled with `changetype:feature` and has the title `Refactor endpoints`:

```
[berto@g6]$ issue-branch 54

[berto@g6]$ git branch | grep '^*'
* feature/54-refactor-endpoints
```
