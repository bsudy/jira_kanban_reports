#!/usr/bin/env python

import pprint
import datetime
import dateutil.parser
import pytz
from business_duration import businessDuration
import holidays as pyholidays
import jira_api
from collections import defaultdict


weekly_man_days= {
    '2018_35_default': {
        'andrei': 5,
        'barny': 5,
        'jan': 5,
        'martin': 5,
        'raffaele': 5,
    },
    '2018_40': {
        'andrei': 5,
        'barny': 5,
        'jan': 5,
        'martin': 5,
        'raffaele': 5,
    },
    '2018_41': {
        'andrei': 5,
        'barny': 3,
        'jan': 5,
        'martin': 5,
        'raffaele': 5,
    },
    '2018_42': {
        'andrei': 5,
        'barny': 3,
        'jan': 5,
        'martin': 1,
        'raffaele': 5,
    },
}

def calculate_velocity(issues):
    velocity = defaultdict(lambda: 0)
    for issue in issues:
        if issue.get('finished') and issue.get('story_points'):
            year, month, _ = issue['finished'].isocalendar()
            velocity['{}_{}'.format(year, month)] += issue.get('story_points')
    return dict(velocity)

def main():

    STATS_FROM = '2018-08-27'
    STATS_FROM_DATE = datetime.datetime.strptime(STATS_FROM, '%Y-%m-%d')
    STATS_FROM_DATE = STATS_FROM_DATE.replace(tzinfo=pytz.utc)
    STAT_PARAM = 'normalized_lead_time'
    # STAT_PARAM = 'lead_time_hours'
    EXTREM_OUTLIER_MULTIPLIER = 2
    OUTLIER_MULTIPLIER = EXTREM_OUTLIER_MULTIPLIER - 1
    now = datetime.datetime.utcnow()
    now = now.replace(tzinfo=pytz.utc) # 27.08
    results = [ 
        res for res in jira_api.get_issue_stats('project = Fullstack and labels = admin-experience and labels != exclude-ax-stats and updated >= {}'.format(STATS_FROM)) 
        if (res.get('finished') or now) > STATS_FROM_DATE
        and res.get('resolution') != 'Cannot Reproduce'
        and res.get('type') != 'Epic'
    ]

    import numpy
    
    velocity = calculate_velocity(results)
    print '---------- Velocity --------------'
    pprint.pprint(velocity)

    import matplotlib.pyplot as plot
    plot.subplot(2, 1, 1)
    plot.title('Velocity')
    plot.plot(velocity.keys(), velocity.values(), 'ro')
    plot.axis([0, 6, 0, 20])
    # plot.show()

    plot.subplot(2, 1, 2)
    plot.title('Lead time distribution')


    normalized_lead_times = [ res.get(STAT_PARAM) for res in results if res.get(STAT_PARAM) != None ]
    mean_lead_time = numpy.mean(normalized_lead_times)
    stdev_lead_time = numpy.std(normalized_lead_times)

    tasks_to_check = []
    extreme_outliers = []
    outliers = []
    normal_tasks = []
    for res in results:
        if res.get(STAT_PARAM) != None:
            if not ((mean_lead_time - EXTREM_OUTLIER_MULTIPLIER * stdev_lead_time) < res.get(STAT_PARAM) < (mean_lead_time + EXTREM_OUTLIER_MULTIPLIER*stdev_lead_time)):
                if not res.get('accepted_outlier', False):
                    extreme_outliers.append(res)
            elif not ((mean_lead_time - OUTLIER_MULTIPLIER  *stdev_lead_time) < res.get(STAT_PARAM) < (mean_lead_time + OUTLIER_MULTIPLIER*stdev_lead_time)):
                if not res.get('accepted_outlier', False):
                    outliers.append(res)
            else:
                normal_tasks.append(res)
        else:
            if res.get('started') != None \
            and res.get('story_points') is None \
            and (res.get('type') != 'Bug' or 'ax-estimable' in res.get('labels', [])):
                tasks_to_check.append(res)

    print '------------------ BASIC STATS ---------------'
    print 'Extream outliers:', len(extreme_outliers)
    print 'Outliers:', len(outliers)
    print 'Normal tasks:', len(normal_tasks)
    print '------------------ EXTREME OUTLIERS ---------------'
    pprint.pprint(extreme_outliers)
    print '------------------ OUTLIERS ---------------'
    pprint.pprint(outliers)
    print '------------------ TASK WITHOUT ENOUGH INFORMATION -------------'
    pprint.pprint(tasks_to_check)
    

    # import matplotlib.pyplot as plot

    counts, bins, bars = plot.hist(
        normalized_lead_times,
        density=1, 
        bins=20,
    )

    for patch, rightside, leftside in zip(bars, bins[1:], bins[:-1]):
        if rightside < (mean_lead_time - EXTREM_OUTLIER_MULTIPLIER * stdev_lead_time):
            patch.set_facecolor('red')
        elif rightside < (mean_lead_time - OUTLIER_MULTIPLIER * stdev_lead_time):
            patch.set_facecolor('orange')
        elif leftside > (mean_lead_time + OUTLIER_MULTIPLIER * stdev_lead_time):
            patch.set_facecolor('orange')
        elif leftside > (mean_lead_time + EXTREM_OUTLIER_MULTIPLIER * stdev_lead_time):
            patch.set_facecolor('red')
       
   
    plot.show()




if __name__ == '__main__':
    main()