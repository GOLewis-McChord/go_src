from src.scripts.route.route import *
from src.scripts.stop.stop import Stop
from src.scripts.web.stop_kml import publish_stop_kml
from src.scripts.web.web_schedule import publish_schedules
from src.scripts.web.web_timetable import publish_time_tables
from src.scripts.utils.functions import stack
from src.scripts.utils.time import *


def build_tables(date):
    web_schedule = {}
    time_table = {}
    stop_table = {}

    # Add StopTime object values to the correct DS
    for stoptime in load(date)[1]:

        if stoptime.destination:
            continue

        # Define terms
        schedule = Schedule.objects[stoptime.trip.schedule]
        segment = Segment.objects[stoptime.trip.segment]
        segment_order = list(schedule.segments.keys())[list(schedule.segments.values()).index(segment)]
        joint = schedule.joint.id
        service_text = schedule.joint.service.text
        start = schedule.start
        end = schedule.end
        headway = schedule.joint.headway
        route = segment.route
        direction = re.sub('to ', '', stoptime.trip.head_sign)
        load_seq = stoptime.order
        stop = stoptime.stop
        time = stoptime.depart_24p
        stop_key = (stop, Stop.objects[stop].name)
        route_key = (route, segment_order)

        # Web schedule DS ----------------------------------------------------------------------------------------------
        if route not in web_schedule:
            web_schedule[route] = {}

        # Set joint attributes, update any improvements to start/end time for schedule
        if joint not in web_schedule[route]:
            web_schedule[route][joint] = {
                'service_text': service_text,
                'start': start,
                'end': end,
                'headway': headway,
                'segments': {}
            }
        else:
            if start < web_schedule[route][joint]['start']:
                web_schedule[route][joint]['start'] = start
            if end > web_schedule[route][joint]['end']:
                web_schedule[route][joint]['end'] = end

        # Add segment_order
        if segment_order not in web_schedule[route][joint]['segments']:
            web_schedule[route][joint]['segments'][segment_order] = {
                'origins': {},
                'directions': {},
            }
        # Update origins and directions
        if load_seq == 0:
            web_schedule[route][joint]['segments'][segment_order]['origins'][Stop.objects[stop].name] = True
        web_schedule[route][joint]['segments'][segment_order]['directions'][direction] = True

        # Add stop, update any improvements to load_seq
        if stop not in web_schedule[route][joint]['segments'][segment_order]:
            web_schedule[route][joint]['segments'][segment_order][stop] = {
                'load_seq': load_seq,
                'times': {}
            }
        elif load_seq > web_schedule[route][joint]['segments'][segment_order][stop]['load_seq']:
            web_schedule[route][joint]['segments'][segment_order][stop]['load_seq'] = load_seq

        # Add time
        web_schedule[route][joint]['segments'][segment_order][stop]['times'][time] = True

        # Time table DS ------------------------------------------------------------------------------------------------
        if stop_key not in time_table:
            time_table[stop_key] = {}
        if route_key not in time_table[stop_key]:
            time_table[stop_key][route_key] = {
                'directions': {}
            }
        time_table[stop_key][route_key]['directions'][direction] = True
        if service_text not in time_table[stop_key][route_key]:
            time_table[stop_key][route_key][service_text] = {}
        time_table[stop_key][route_key][service_text][time] = True

    web_schedule = convert_schedule(web_schedule)
    time_table = convert_time_table(time_table)

    # Stop table DS ------------------------------------------------------------------------------------------------
    # Iterate through web schedule and pass over objects to new format
    for route in web_schedule:
        for joint in web_schedule[route]:
            service_text = web_schedule[route][joint]['service_text']
            start = web_schedule[route][joint]['start']
            end = web_schedule[route][joint]['end']
            for segment in web_schedule[route][joint]['segments']:
                directions = ', '.join(web_schedule[route][joint]['segments'][segment]['directions'])
                for load_seq in web_schedule[route][joint]['segments'][segment]:
                    if load_seq == 'origins' or load_seq == 'directions':
                        continue
                    stop = web_schedule[route][joint]['segments'][segment][load_seq]
                    new_stop_key = (stop['id'], stop['name'], Stop.objects[stop['id']].lat,
                                    Stop.objects[stop['id']].lng)

                    # Load into stop_table
                    if new_stop_key not in stop_table:
                        stop_table[new_stop_key] = {}
                    stop_table[new_stop_key][(route, service_text, start, end, directions)] = stop['times']

    return web_schedule, time_table, stop_table


def convert_schedule(web_schedule):
    for route in web_schedule:
        for joint in web_schedule[route]:
            obj = web_schedule[route][joint]

            # Figure out the number of trips there should be
            count = round((obj['end'] - obj['start']).total_seconds() / obj['headway'])

            # If the route operates less than two hours or does not have an even headway
            if (obj['end'] - obj['start']).total_seconds() < 7200 or count < 6:
                web_schedule[route][joint] = convert_many_to_list(obj)

            # For routes that have a headway that is equally divisible into hour sections
            elif 3600 % obj['headway'] == 0:

                for order in obj['segments']:

                    # Iterate through each load_seq to determine if it qualifies for xx:NN simplified time
                    for stop in list(obj['segments'][order].keys()):
                        if stop == 'origins' or stop == 'directions':
                            continue

                        times = obj['segments'][order][stop]['times']

                        # If the headway timing test passes, convert to xx:00 time
                        if test_timing_headways(times, obj['headway']) and (count - 2) < len(times) < (count + 2):
                            web_schedule[route][joint]['segments'][order][stop]['times'] = (convert_to_xx(times))

                        # Else move to the exceptions dict for the Route
                        else:
                            web_schedule[route][joint]['segments'][order][stop]['times'] = (convert_to_list(times))

            # Convert data structure for final usage
            for order in obj['segments']:
                for stop in list(obj['segments'][order].keys()):
                    if stop == 'origins' or stop == 'directions':
                        continue
                    # Set key to load_seq
                    obj['segments'][order][obj['segments'][order][stop]['load_seq']] = {
                        'id': stop,
                        'loc': stop[:3],
                        'gps_ref': stop[3],
                        'name': Stop.objects[stop].name,
                        'times': obj['segments'][order][stop]['times']
                    }
                    del obj['segments'][order][stop]

    return web_schedule


def convert_time_table(time_table):
    for stop_key in time_table:
        for route_key in time_table[stop_key]:
            for service_text in time_table[stop_key][route_key]:
                if service_text == 'directions':
                    continue
                time_table[stop_key][route_key][service_text] = stack(convert_to_list(
                    time_table[stop_key][route_key][service_text]), 2, 'column', 'column')
    return time_table


def convert_many_to_list(obj):
    for order in obj['segments']:
        for stop in obj['segments'][order]:
            if stop == 'origins' or stop == 'directions':
                continue
            # Create an ordered list of times in 24 hour time
            obj['segments'][order][stop]['times'] = convert_to_list(obj['segments'][order][stop]['times'])
    return obj


def convert_to_list(times):
    return [convert_to_24_time(time, seconds=False) for time in sorted(times.keys())]


def test_timing_headways(times, headway):
    # Collect stop times and set the first one to the prev key
    test = True
    times = sorted(times.keys())
    prev = datetime.datetime.strptime(times[0], '%H:%M:%S')

    # Iterate through the keys and check that each progression is exactly a headway apart
    for time in times[1:]:
        prev += datetime.timedelta(seconds=headway)
        if datetime.datetime.strptime(time, '%H:%M:%S') != prev:
            test = False

    return test


def convert_to_xx(times):
    new_times = {}
    for time in times:
        new_times['xx:{}'.format(time[3:5])] = True
    return sorted(new_times.keys())


def publish(date=datetime.datetime.today()):
    web_schedule, time_table, stop_table = build_tables(date)
    publish_schedules(web_schedule)
    publish_time_tables(time_table)
    publish_stop_kml(stop_table)


if __name__ == "__main__":
    publish()