import pprint
import datetime
import dateutil.parser
import pytz
from business_duration import businessDuration
import holidays as pyholidays
import jira_api
from collections import defaultdict
from collections import OrderedDict
import numpy
import math
import operator
import copy

STATS_FROM = '2018-08-27'
STATS_FROM_DATE = datetime.datetime.strptime(STATS_FROM, '%Y-%m-%d')
STATS_FROM_DATE = STATS_FROM_DATE.replace(tzinfo=pytz.utc)
STAT_PARAM = 'normalized_lead_time'
EXTREM_OUTLIER_MULTIPLIER = 2
OUTLIER_MULTIPLIER = EXTREM_OUTLIER_MULTIPLIER - 1

PERSON_DAYS_PER_WEEK = {
    'default': {
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
    '2018_43': {
        'andrei': 5,
        'barny': 3,
        'jan': 5,
        'martin': 5,
        'raffaele': 5,
    },
    '2018_44': {
        'andrei': 5,
        'barny': 3,
        'jan': 5,
        'martin': 5,
        'raffaele': 5,
    },
    '2018_45': {
        'andrei': 5,
        'barny': 3,
        'jan': 5,
        'martin': 5,
        'raffaele': 5,
    },
    '2018_46': {
        'andrei': 5,
        'barny': 3,
        'jan': 5,
        'martin': 5,
        'raffaele': 5,
    },
    '2018_47': {
        'andrei': 5,
        'barny': 3,
        'jan': 5,
        'martin': 5,
        'raffaele': 5,
    },
    '2018_48': {
        'andrei': 5,
        'barny': 3,
        'jan': 5,
        'martin': 5,
        'raffaele': 5,
    },
    '2018_49': {
        'andrei': 5,
        'barny': 3,
        'jan': 5,
        'martin': 5,
        'raffaele': 5,
    },
    '2018_50': {
        'andrei': 5,
        'barny': 3,
        'jan': 5,
        'martin': 5,
        'raffaele': 5,
    },
    '2018_51': {
        'andrei': 5,
        'barny': 3,
        'jan': 5,
        'martin': 5,
        'raffaele': 5,
    },
}

def normalize_velocity(velocity_dict):
    normalized_velocity = copy.deepcopy(velocity_dict)

    for date, velocity in velocity_dict.items():
        sum_person_days = None
        if PERSON_DAYS_PER_WEEK.get(date):
            sum_person_days = sum(PERSON_DAYS_PER_WEEK.get(date).values())
        else:
            sum_person_days = sum(PERSON_DAYS_PER_WEEK['default'].values())
        normalized_velocity[date] = velocity/sum_person_days
    return normalized_velocity


def _calculate_velocity(issues):
    start = STATS_FROM_DATE
    now = datetime.datetime.utcnow()
    end = now.replace(tzinfo=pytz.utc)  # 27.08
    dates = [
        start + datetime.timedelta(days=x)
        for x in range(0, (end-start).days)
    ]
    velocity = OrderedDict(sorted(
        {
            '{}_{}'.format(*d.isocalendar()[0:2]): 0
            for d in dates
        }.items(),
        key=operator.itemgetter(0),
    ))

    for issue in issues:
        if issue.get('finished') and issue.get('story_points'):
            year, month, _ = issue['finished'].isocalendar()
            velocity['{}_{}'.format(year, month)] += issue.get('story_points')
    return velocity


def _get_issues():
    now = datetime.datetime.utcnow()
    now = now.replace(tzinfo=pytz.utc)  # 27.08
    issues = [
        res for res in jira_api.get_issue_stats(
            'project = Fullstack and labels = admin-experience and labels != exclude-ax-stats and updated >= {}'.format(
                STATS_FROM))
        if (res.get('finished') or now) > STATS_FROM_DATE
           and res.get('resolution') != 'Cannot Reproduce'
           and res.get('type') != 'Epic'
    ]
    return issues


def _print_stats(issues, mean_lead_time, normalized_lead_times,
                 stdev_lead_time):
    tasks_to_check = []
    extreme_outliers = []
    outliers = []
    normal_tasks = []
    for res in issues:
        if res.get(STAT_PARAM) != None:
            if not ((
                            mean_lead_time - EXTREM_OUTLIER_MULTIPLIER * stdev_lead_time) < res.get(
                    STAT_PARAM) < (
                            mean_lead_time + EXTREM_OUTLIER_MULTIPLIER * stdev_lead_time)):
                if not res.get('accepted_outlier', False):
                    extreme_outliers.append(res)
            elif not ((
                              mean_lead_time - OUTLIER_MULTIPLIER * stdev_lead_time) < res.get(
                    STAT_PARAM) < (
                              mean_lead_time + OUTLIER_MULTIPLIER * stdev_lead_time)):
                if not res.get('accepted_outlier', False):
                    outliers.append(res)
            else:
                normal_tasks.append(res)
        else:
            if res.get('started') != None \
                    and res.get('story_points') is None \
                    and (res.get('type') != 'Bug' or 'ax-estimable' in res.get(
                'labels', [])) \
                    and (
                    res.get('type') != 'Sub-task' or 'ax-estimable' in res.get(
                'labels', [])):
                tasks_to_check.append(res)
    print('------------------ BASIC STATS ---------------')
    print('Extream outliers:', len(extreme_outliers))
    print('Outliers:', len(outliers))
    print('Normal tasks:', len(normal_tasks))
    print('------------------ EXTREME OUTLIERS ---------------')
    pprint.pprint(extreme_outliers)
    print('------------------ OUTLIERS ---------------')
    pprint.pprint(outliers)
    print('------------------ TASK WITHOUT ENOUGH INFORMATION -------------')
    pprint.pprint(tasks_to_check)
    print('Min', min(normalized_lead_times))
    print('Max', max(normalized_lead_times))
    print(normalized_lead_times)


def _handle_velocity(issues, normalized_lead_times, mean_lead_time, stdev_lead_time):
    import matplotlib.pyplot as plot
    velocity = _calculate_velocity(issues)

    print('---------- Velocity --------------')
    pprint.pprint(velocity)

    plot.subplot(2, 1, 1)
    plot.title('Velocity')
    n_velocity = normalize_velocity(velocity)
    v_plot = plot.plot(n_velocity.keys(), n_velocity.values())
    plot.setp(v_plot, color='r', linewidth=1.0)
    plot.axis('auto')
    plot.locator_params(nbins=10)
    plot.xticks(rotation=90)

    plot.subplot(2, 1, 2)
    plot.title('Lead time distribution')
    counts, bins, bars = plot.hist(
        normalized_lead_times,
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
    return plot


def main():

    issues = _get_issues()
    normalized_lead_times = sorted([
        res.get(STAT_PARAM)
        for res in issues
        if res.get(STAT_PARAM)
           and (not math.isnan(res.get(STAT_PARAM)))
    ])
    mean_lead_time = numpy.mean(normalized_lead_times)
    stdev_lead_time = numpy.std(normalized_lead_times)
    plot = _handle_velocity(
        issues,
        normalized_lead_times,
        mean_lead_time,
        stdev_lead_time,
    )

    _print_stats(issues, mean_lead_time, normalized_lead_times, stdev_lead_time)
    plot.show()


if __name__ == '__main__':
    main()
