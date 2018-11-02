#!/usr/bin/env python

import pprint
import datetime
import dateutil.parser
import pytz
from business_duration import businessDuration
import holidays as pyholidays
import jira_api
import dateutil.parser


def get_issue_stats(jql):
    
    issues = jira_api.get_issues(jql)

    counter = 0
    for issue in issues:
        # print '---------------------'
        # pprint.pprint(issue)
        counter += 1

        transitions = list(jira_api.get_transitions(issue))
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
            'current_status': (issue.get('fields', {}).get('status', {}) or {}).get('name'),
            'priority': (issue.get('fields', {}).get('priority', {}) or {}).get('name'),
            'severity': (issue.get('fields', {}).get('customfield_11339', {}) or {}).get('value'),
            'created': dateutil.parser.parse(issue.get('fields', {}).get('created')),
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

def main():

    STATS_FROM = '2018-08-27'
    STATS_FROM_DATE = datetime.datetime.strptime(STATS_FROM, '%Y-%m-%d')

    now = datetime.datetime.utcnow()
    now = now.replace(tzinfo=pytz.utc)

    results = [ 
        res for res in get_issue_stats('project = Fullstack and labels = admin-experience and labels != exclude-ax-stats and type = BUG') 
        if res.get('resolution') != 'Cannot Reproduce'
    ]


    state_counter = {}
    created_last_week = 0
    solved_last_week = 0
    for result in results:
        # print '------------------------------'
        # pprint.pprint(result)
        if result['current_status'] in state_counter:
            state_counter[result['current_status']]['counter'] += 1
        else:
            state_counter[result['current_status']] = { 'counter': 1, 'priorities': {}, 'severities': {} }

        def update_counter(status, div, counter):
            if counter in state_counter[status][div]:
                state_counter[status][div][counter] += 1
            else:
                state_counter[status][div][counter] = 1
        
        update_counter(result['current_status'], 'priorities', result['priority'] if result['priority'] else 'Not set')
        update_counter(result['current_status'], 'severities', result['severity'] if result['severity'] else 'Not set')

        if result['created'] > (now - datetime.timedelta(weeks=1)):
            print '------- NEW BUG'
            pprint.pprint(result)
            created_last_week += 1
        if result.get('finished') and result['finished'] > (now - datetime.timedelta(weeks=1)):
            solved_last_week += 1
            print '------- SOLVED BUG'
            pprint.pprint(result)

    print '------------------------------'
    # pprint.pprint(state_counter)

    def get_counts(*state):
        result = 0
        for s in state:
            result += state_counter.get(s, {}).get('counter', 0)
        return result

    def get_sub_counts(div, *state):
        results = {}
        for s in state:
            sub_counts = state_counter.get(s, {}).get(div, {})
            for k, v in sub_counts.iteritems():
                if k in results:
                    results[k] += v
                else:
                    results[k] = v
        return results

    print '--------------------------------------------'
    print 'Shipped: {}'.format(get_counts('Done', 'QA'))
    print 'In Progress: {}'.format(get_counts('In Progress'))
    print 'Unresolved: {}'.format(get_counts('Confirmed', 'To Do', 'Info Needed', 'Input Needed', 'On Hold', 'Triage Needed') )
    print '   Priorities: {}'.format(get_sub_counts('priorities', 'Confirmed', 'To Do'))
    print '   Severities: {}'.format(get_sub_counts('severities', 'Confirmed', 'To Do'))
    print '   ----------------------------------'
    print '   ToDo: {}'.format(get_counts('Confirmed', 'To Do'))
    print '   Blocked: {}'.format(get_counts('Info Needed', 'Input Needed', 'On Hold', 'Triage Needed'))
    print '--------------------------------------------'
    print 'Created last week: {}'.format(created_last_week)
    print 'Solved last week:  {}'.format(solved_last_week)
    print 'Change last week:  {}'.format(created_last_week - solved_last_week)


if __name__ == '__main__':
    main()