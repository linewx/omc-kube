import humanize
import datetime

def fromisotime(the_time):
    if isinstance(the_time, datetime.datetime):
        return the_time
    elif isinstance(the_time, str):
        if the_time.endswith('Z'):
            the_time = the_time[:-1]
        return datetime.datetime.fromisoformat(the_time)


def calculate_age(the_time):
    return humanize.naturaldelta(the_time, when=datetime.datetime.now(), months=False)
