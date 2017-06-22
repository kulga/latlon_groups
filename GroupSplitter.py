#!/usr/bin/python3

import argparse
import math 
import csv
import sys
import logging
logging.basicConfig(level=logging.DEBUG, stream=sys.stderr, format='%(asctime)s - %(levelname)s - %(message)s')

from pprint import PrettyPrinter
from random import choice

# 3rd party - Plotting
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np

# Local - decorator
from decorators import logging_decorator

class GroupSplitter():
    '''
    Take csv file of users and their lat long and split into even groups
    '''
    def __init__(self, csvfile, groups=2, loglevel=4):
        self.csvfile = csvfile
        self.groups = groups
        self.loglevel = loglevel

        loglevels = {
                0: None,
                5: logging.DEBUG,
                4: logging.INFO,
                3: logging.WARNING,
                2: logging.ERROR,
                1: logging.CRITICAL }
        if loglevels[loglevel]:
            logging.getLogger().setLevel(loglevels[loglevel])
        else:
            logging.disable(logging.CRITICAL)

        # Read list of users
        users = list()
        for file in self.csvfile:
            users.extend(self.__read_csv(file))
        self.num_per_group = int(math.ceil(len(users) / int(groups)))

        self.built_groups = self.__build_groups(users, self.groups)

        for index, group in enumerate(self.built_groups):
            logging.info('Group {index}:  Members {number}'.format(
            index=index,
            number=len(group)))


    @logging_decorator
    def print_group(self, _format):
        import json, csv, pprint

        def output_data(built_groups):
            groups = dict()
            for index, group in enumerate(built_groups):
                groups[index] = [user['id'] for user in group]
            return groups

        def print_pprint(_dict):
            pp = PrettyPrinter(indent=1, width=80)
            pp.pprint(_dict.items())

        def print_json(_dict):
            print(json.dumps(_dict, ensure_ascii=False))

        def print_csv(_dict):
            fieldnames = ['Group', 'Names']
            writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
            writer.writeheader()

            for Group, Names in _dict.items():
                writer.writerow({
                    'Group': 'Group{}'.format(Group),
                    'Names': ' '.join([name for name in Names])})

        formats = {
                'pprint': print_pprint,
                'json': print_json,
                'csv': print_csv }

        formats[_format](output_data(self.built_groups))



    @logging_decorator
    def plot_map(self):
        """
        Generate visual map of plotted users
        """
        # Evenly sequenced numbers for scatter plot
        colors = cm.rainbow([
            0 + x*(1-0)/len(self.built_groups) 
            for x in range(len(self.built_groups))])
        np.random.shuffle(colors)
        colors = iter(colors)

        markers = ['+','o','*','.','x','s','d','^','v','>','<','p','h']

        plotids = list()
        for index, groups in enumerate(self.built_groups):
            color = next(colors)
            x_values = list()
            y_values = list()
            for user in groups:
                y, x = user['latlon']
                x_values.append(float(x))
                y_values.append(float(y))

            plotid = plt.scatter(x_values, y_values, 
                    color=color, 
                    picker=True, 
                    marker=choice(markers),
                    label=str(user['id']))
            plotids.append((index, plotid))

        plt.legend(
            [group[1] for group in plotids],
            ['Group {}'.format(group[0]) for group in plotids],
            loc = 'lower left',
            scatterpoints=1)
        plt.show()


    @logging_decorator
    def __read_csv(self, csv_file):
        with open(csv_file) as csv_users:
            reader = csv.DictReader(csv_users)
            users = list()

            skipped_users=0
            try:
                for user in reader:
                    if all(key in user.keys() for key in ['id', 'latitude', 'longitude']):
                        try:
                            user['latlon'] = (float(user['latitude']), float(user['longitude']))
                            users.append(user)
                        except ValueError:
                            skipped_users += 1

                    else:
                        logging.critical('''Data is not formatted correctly!\nCannot find some of these headers:
                            {}
                            {}
                            {}'''.format( 'id', 'latitude', 'longitude'))
                        sys.exit()
                if skipped_users > 0:
                    logging.warning('Skipped {rows} rows due to missing values'.format(rows=skipped_users))
            except UnicodeDecodeError as error:
                logging.critical( 'Are you sure {file} is a CSV file?\n{}'.format(error, file=str(csv_file)))
                sys.exit()
        return users


    @logging_decorator
    def __distance(self, A, B):
        """
        Accepts two tuples (lat, long) of latitude and longitude
        To identify distances
        """

        a_lat, a_long = A
        b_lat, b_long = B

        x = (b_long - a_long) * math.cos((a_lat + b_lat) / 2)
        y = b_lat - a_lat
        distance = math.sqrt(x ** 2 + y ** 2) * 6371

        return distance


    @logging_decorator
    def __build_groups(self, user_list, groups=2):
        """
        Splits user_list into n groups
        """

        # Make copy of user_list and sort it by longitude, west -> east
        user_list_copy = sorted(
                list(user_list), 
                key=lambda lon: lon['latlon'][1])

        groups_list = list()
        num_groups = 0 # Start matching from this user. Should == number of groups

        while num_groups <= int(groups) - 1: # subtract 1 to match starting at 0
            user = user_list_copy[num_groups]

            current_group = list()
            for other_user in sorted(user_list_copy, 
                    key=lambda other_user: self.__distance(user['latlon'], other_user['latlon'])
                    ):
                if len(current_group) <= self.num_per_group:
                    current_group.append(other_user)
                    del(user_list_copy[user_list_copy.index(other_user)])
                else:
                    break
            if current_group and len(current_group) >= self.num_per_group:
                groups_list.append(current_group)
                num_groups += 1 # Group has been filled, increment
            else:
                groups_list[-1].extend(current_group)

                # After merge into previous group, see if previous group
                # is 1.5X the size of the max number per group.
                # If it is, split it and append it as a new group
                if len(groups_list[-1]) >= self.num_per_group * 1.5:
                    splitting_group = groups_list[-1][self.num_per_group:]
                    del(groups_list[-1][self.num_per_group:])
                    groups_list.append(splitting_group)
                    num_groups += 1 # Group has been split, increment

        return groups_list


    @logging_decorator
    def write_csv(self, output_file):
        '''
        Write csv file of groups and their users
        '''
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['Group', 'Names']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            logging.info('Writing to file {}'.format(output_file))

            for index, group in enumerate(self.built_groups):
                Names = ' '.join([user['id'] for user in group])
                Group = index
                writer.writerow({
                    'Group': 'Group {}'.format(Group),
                    'Names': Names})




def main():
    # Create commandline flags
    parser = argparse.ArgumentParser(description='Groups users by their latitude, longitude')
    parser.add_argument('-f', '--file',
            required=True,
            action='append',
            help='Parse CSV file. Must include headers: name, latitude, longitude')
    parser.add_argument('-g', '--groups',
            default=2,
            help='Set desired number of groups. Will be split as evenly as possible')
    parser.add_argument('-o', '--output',
            help='Write to file in csv format')
    parser.add_argument('--print-user-groups',
            choices=['pprint', 'json', 'csv'],
            default=None,
            help='Print out list of groups to terminal')
    parser.add_argument('--plot',
            action='store_true',
            help='Show colored visual plot map of groups')
    parser.add_argument('--loglevel',
            type=int,
            choices=[0, 1, 2, 3, 4, 5],
            default=4,
            help='Increase level for more verbosity. 0 diables logging')
    args = parser.parse_args()

    primary_group = GroupSplitter(
            args.file, 
            groups=args.groups, 
            loglevel=args.loglevel)

    if args.output:
        primary_group.write_csv(args.output)

    if args.print_user_groups:
        primary_group.print_group(args.print_user_groups)

    if args.plot:
        primary_group.plot_map()


if __name__ == '__main__':
    main()

