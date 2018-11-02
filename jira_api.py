import requests
import pprint
import datetime
import dateutil.parser
import pytz
import os
from business_duration import businessDuration
import holidays as pyholidays


import ConfigParser
config = ConfigParser.RawConfigParser()
config.read(os.path.expanduser('~/.jira.properties'))


BASE_URL = config.get('JIRA', 'BASE_URL')
API_TOKEN = config.get('JIRA', 'API_TOKEN')
USER = config.get('JIRA', 'USER')

HEADERS={
    'Accept': 'application/json',
}


def get_issues(jql):
    
    startAt = 0

    while True:
    
        params={
            'jql': jql,
            'startAt': startAt,
            'expand': 'transitions,changelog',
        }
    
        r = requests.get(
            '{}{}'.format(BASE_URL, 'search'), 
            params=params, 
            headers=HEADERS,
            auth=(USER, API_TOKEN))

        response = r.json()
        for issue in response.get('issues'):
            yield issue

        if len(response.get('issues', [])) == response.get('maxResults'):
            startAt += len(response.get('issues', []))
        else:
            return
        # return

def get_transitions(issue):
    history = issue.get('changelog', {}).get('histories', [])

    for history_item in history:
        for changed_item in history_item.get('items', []):
            if changed_item.get('field') == 'status':
                yield {
                    'from': changed_item.get('fromString'),
                    'to': changed_item.get('toString'),
                    'at': dateutil.parser.parse(history_item.get('created'))
                }
                    


def get_issue_stats(jql):
    
    issues = get_issues(jql)

    counter = 0
    for issue in issues:
        # print '---------------------'
        # pprint.pprint(issue)
        counter += 1

        transitions = list(get_transitions(issue))
        transitions = sorted(transitions, key=lambda tr: tr.get('at'))
        
        started = None
        finished = None
        back_from_finished = False

        for transition in transitions:
            # pprint.pprint(transition)
            if transition.get('to') == 'In Progress':
                if started == None:
                    started = transition.get('at')
            elif transition.get('to') == 'To Do' or transition.get('to') == 'New':
            # or transition.get('to') == 'Input Needed':
                if finished == None and started != None:
                    started = None
                elif finished != None:
                    back_from_finished = True
            elif transition.get('to') == 'QA':
                back_from_finished = False
                if started != None:
                    finished = transition.get('at')
            elif transition.get('to') == 'Done':
                back_from_finished = False
                if finished == None or back_from_finished:
                    finished = transition.get('at')

        result = {
            'issue': issue.get('key'),
            'link': "https://beekeeper.atlassian.net/browse/{}".format(issue.get('key')),
            'type': issue.get('fields', {}).get('issuetype', {}).get('name'),
            'story_points': issue.get('fields', {}).get('customfield_10005'),
            'started': started,
            'finished': finished if not back_from_finished else None,
            'lead_time_hours': None,
            'normalized_lead_time': None,
            'resolution': (issue.get('fields', {}).get('resolution') or {}).get('name'),
            'summary': issue.get('fields', {}).get('summary'),
            'accepted_outlier': 'ax-stats-outlier' in issue.get('fields', {}).get('labels', []),
            'labels': issue.get('fields', {}).get('labels', []),
        }


        #Business open hour
        biz_open_time = datetime.time(9,0,0)

        #Business close time
        biz_close_time = datetime.time(18,0,0)
        weekend_list = [5,6]
        holidaylist = pyholidays.Switzerland()

        if started != None and finished != None:
            result['lead_time_hours'] = businessDuration(
                startdate=started, 
                enddate=finished, 
                starttime=biz_open_time,
                endtime=biz_close_time,
                weekendlist=weekend_list,
                holidaylist=holidaylist,
                unit='hour')

        if result.get('lead_time_hours') != None and result.get('story_points') != None and result.get('story_points') > 0:
            result['normalized_lead_time'] = result.get('lead_time_hours') / result.get('story_points')

        yield result

    # print counter
