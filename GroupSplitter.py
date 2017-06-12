#!/usr/bin/python3

# Python2 support
# https://docs.python.org/3/reference/simple_stmts.html#future-statements
from __future__ import absolute_import, division, generators, unicode_literals, print_function, nested_scopes, with_statement

import argparse
import math
import csv

from pprint import PrettyPrinter
from random import choice
from operator import itemgetter

# 3rd party - Plotting
import matplotlib.pyplot as plt
import matplotlib.cm as cm

class GroupSplitter():
    '''
    Take csv file of users and their lat long and split into even groups
    '''
    def __init__(self, csvfile, groups=2, quiet=False):
        self.csvfile = csvfile
        self.groups = groups
        self.quiet = quiet

        # Read list of users
        users = list()
        for file in self.csvfile:
            users += self.__read_csv(file)
        self.num_per_group = int(math.ceil(len(users) / int(groups)))

        self.built_groups = self.__build_groups(users, self.groups)
        if not self.quiet:
            for index, group in enumerate(self.built_groups):
                print('Group {index}: {number} members'.format(
                index=index,
                number=len(group)))


    def print_group(self):
        for index, group in enumerate(self.built_groups):
            # Print out each group and its users
            pp = PrettyPrinter(indent=4)
            pp.pprint('Group:{group} Users:{users}'.format(
                group=index,
                users=[user['name'] for user in group]))


    def plot_map(self):
        """
        Generate visual map of plotted users
        """
        # Evenly sequenced numbers for scatter plot
        colors = iter(cm.rainbow([
            0 + x*(1-0)/len(self.built_groups) 
            for x in range(len(self.built_groups))]))
        markers = ['x', '^', '*']

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
                    label=str(user['name']))
            plotids.append((index, plotid))

        plt.legend(
            [group[1] for group in plotids],
            ['Group {}'.format(group[0]) for group in plotids],
            loc = 'lower left',
            scatterpoints=1)
        plt.show()


    def __read_csv(self, file):
        with open(file) as csv_users:
            reader = csv.reader(csv_users)
            try:
                header = [item.lower() for item in next(reader)]
            except UnicodeDecodeError as error:
                print( 'I got a error!\nAre you sure this is a CSV file?\n\n{}'.format(error))
                exit(1)

            if (
                    'name' in header
                    and 'latitude' in header 
                    and 'longitude' in header
               ):
                name = header.index('name')
                lat = header.index('latitude')
                lon = header.index('longitude')
                    
                skipped_users = 0
                users = list()
                for user in reader:
                    try:
                        profile = {
                                'name': str(user[name]),
                                'latlon': (float(user[lat]), float(user[lon]))
                            }
                        users.append(profile)
                    except ValueError:
                        skipped_users += 1

                if skipped_users > 0:
                    print('Skipped {rows} rows due to missing values'.format(rows=skipped_users))
            else:
                print('''Data is not formatted correctly!\nCannot find some of these headers:
                    {}
                    {}
                    {}'''.format( 'name', 'latitude', 'longitude'))
                exit()

        return users


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


    def __build_groups(self, user_list, groups=2):
        """
        Splits user_list into n groups
        """

        # Make copy of user_list and sort it by longitude, west -> east
        user_list_copy = sorted(
                user_list[:], 
                key=lambda lon: lon['latlon'][1])

        groups_list = list()

        for user in user_list_copy:
            current_group = list()
            self.num_per_group = int(math.ceil(len(user_list) / int(groups)))

            for other_user in sorted(user_list_copy, 
                    key=lambda other_user: self.__distance(user['latlon'], other_user['latlon'])
                    ):
                if len(current_group) <= self.num_per_group:
                    current_group.append(other_user)
                    del(user_list_copy[user_list_copy.index(other_user)])
            if current_group and len(current_group) >= self.num_per_group:
                groups_list.append(current_group)
            else:
                groups_list[-1] += current_group

                # After merge into previous group, see if previous group
                # is double the size of the max number per group.
                # If it is, split it and append it as a new group
                if len(groups_list[-1]) >= self.num_per_group * 1.5:
                    splitting_group = groups_list[-1][self.num_per_group:]
                    del(groups_list[-1][self.num_per_group:])
                    groups_list.append(splitting_group)

        return groups_list


    def write_csv(self, output_file):
        '''
        Write csv file of groups and their users
        '''
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['Group', 'Names']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            if not self.quiet:
                print('Writing to file {}'.format(output_file))
            for index, group in enumerate(self.built_groups):
                Names = ' '.join([user['name'] for user in group])
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
    parser.add_argument('--print-group-users',
            default=False,
            action='store_true',
            help='Print text list of groups to terminal')
    parser.add_argument('--plot',
            action='store_true',
            help='Show colored visual plot map of groups')
    parser.add_argument('-q', '--quiet',
            default=False,
            action='store_true',
            help='Disable standard output of groups')
    args = parser.parse_args()

    primary_group = GroupSplitter(
            args.file, 
            groups=args.groups, 
            quiet=args.quiet)

    if args.output:
        primary_group.write_csv(args.output)

    if args.print_group_users:
        primary_group.print_group()

    if args.plot:
        primary_group.plot_map()


if __name__ == '__main__':
    main()

