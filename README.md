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
* ax-estimable - Bugs are not due to estimates by default. With this label, one can mark bigger bugs that should have been estimated.
* exclude-ax-stats - to exclude an issue from the stats.