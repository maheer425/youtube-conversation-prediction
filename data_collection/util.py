#!/usr/bin/python

import os
import json
from collections import defaultdict

def json_dump(content, filename):
	""" Dumps content to json file """
	with open(filename+'.json', 'w') as outfile:
		json.dump(content, outfile, indent = 4, ensure_ascii=True)

def inverted_index(vid_ids_json_cat_dict):
	inv_idx = defaultdict(list)
	for cat_id, vid_ids in vid_ids_json_cat_dict.iteritems():
		for vid_id in vid_ids:
			inv_idx[vid_id].append(cat_id)
	return inv_idx

def prune(inv_idx,failed_list):
	""" Deletes vid_ids from inv_idx if they are in the failed list """
	for failed_vid_id in failed_list:
		del inv_idx[failed_vid_id]
	return inv_idx

if __name__ == "__main__":


	#### The code below converts an old cat vid dict to an inverted index style dict ####
	# os.chdir(os.path.join(os.pardir, 'data')) #go into data folder
	# cat_vid_dict = json.load(open('video_ids_v4.json'))
	# inv_idx = inverted_index(cat_vid_dict)
	# print len(inv_idx)
	# json_dump(inv_idx, 'video_ids_v5')	
	########