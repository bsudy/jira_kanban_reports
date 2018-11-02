# Setup

* Create a API token for jira on [https://id.atlassian.com/manage/api-tokens](https://id.atlassian.com/manage/api-tokens)
* Create a .jira.properties file in your home with the following content:
```
[JIRA]
BASE_URL:<<URL to the API endpoint. eg: https://company.atlassian.net/rest/api/2/>>
USER:<<username: eg. johndoe@company.com>>
API_TOKEN:<<The generated api token>>
```
* Enjoy the scripts

# Jira labels

Supported Jira labels:

* ax-stats-outlier - to mark already accepted outliers

