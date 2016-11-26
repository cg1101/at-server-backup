#!/usr/bin/env python

import sys
import os
import argparse

from jobs import jobs


def run_job(args):
	job_key = args.subcommand.replace('-', '_')
	sys.exit(jobs[job_key](taskId=args.task_id))


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	subparsers = parser.add_subparsers()

	# # TODO: identify current by checking login
	# os.environ['CURRENT_USER_ID'] = ...

	job_parser = subparsers.add_parser('job')
	choices = [name.replace('_', '-') for name in jobs]
	job_parser.add_argument('subcommand', choices=choices)
	job_parser.add_argument('-t', '--task-id', type=int)
	job_parser.set_defaults(func=run_job)

	args = parser.parse_args()
	args.func(args)


if __name__ == '__main__':
	main()
