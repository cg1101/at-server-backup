
jobs = {}

def import_jobs():
	import glob
	import os
	mods = glob.glob(os.path.join(os.path.dirname(__file__), 'job_*.py'))
	for mod_file in mods:
		mod_name = os.path.splitext(os.path.basename(mod_file))[0]
		func_name = mod_name[4:]
		job_mod = __import__(mod_name, globals(), locals(), [], -1)
		jobs[func_name] = job_mod.main

import_jobs()

__all__ = ['jobs']
