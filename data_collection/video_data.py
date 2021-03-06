'''
Input json of vid_ids, ouputs data as json file
'''

from apiclient.discovery import build
from apiclient.discovery import build_from_document
from apiclient.errors import HttpError
import httplib2
import os
import sys
import json
from captions3 import get_formatted_transcript
from util import *


# Authenticate
YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
DEVELOPER_KEY = "AIzaSyBEuuLWPO0AJIIp7TVGIB1uM_mNiNkMVbw"

# Assign
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)


def get_approx_score(vid_id):
	""" Get the approx raw_score of comments from a videoID """
	next_page_tok = None
	score = 0
	while next_page_tok != '':
		# Get the thread via API call
		api_results = youtube.commentThreads().list(
			part 		= "snippet",
			videoId 	= vid_id,
			textFormat	= "plainText",
			maxResults	= 100,
			pageToken 	= next_page_tok
		).execute()

		# Process the thread and get the associated comments
		for item in api_results["items"]:
			num_replies = item["snippet"]["totalReplyCount"]
			# Only add for 2 or more replies
			score = score + num_replies if num_replies >= 2 else score
		
		next_page_tok = api_results["nextPageToken"] if "nextPageToken" in api_results else ''
		next_page_tok = '' if next_page_tok is None else next_page_tok #condition for while loop sanity
	return score


def get_comment_threads(vid_id, data=None, next_page_tok=None):
	""" Get the thread of comments from a videoID """

	def comments_list(parent_id):
		"""Get the comments from a particular thread"""
		api_results = youtube.comments().list(
			part 		= "snippet",
			parentId 	= parent_id,
			textFormat 	= "plainText",
		).execute()
		comments = api_results["items"]
		return comments

	def format_comment(comment):
		""" Format comments """
		return {
			'author': comment["snippet"]["authorDisplayName"],
			'date'	: comment["snippet"]["updatedAt"],
			'text'	: comment["snippet"]["textDisplay"]
		}
	##############################################
	# Check base case
	if next_page_tok == '' or next_page_tok is None and data is not None:
		return data
	# If this is the first call, start data
	if data is None:
		data = {}
	# Get the thread via API call
	api_results = youtube.commentThreads().list(
		part 		= "snippet",
		videoId 	= vid_id,
		textFormat	= "plainText",
		maxResults	= 100,
		pageToken 	= next_page_tok
	).execute()

	# Process the thread and get the associated comments
	for item in api_results["items"]:
		comment_id 	= item["id"]
		top_comment = format_comment(item["snippet"]["topLevelComment"])
		num_replies = item["snippet"]["totalReplyCount"]
		# Only if this has 2 or more replies do I add it
		if num_replies >= 2:
			data[comment_id] = {
				"top_comment"	: top_comment,
				"num_replies"	: num_replies,
				"comments"		: [format_comment(comment) for comment in comments_list(comment_id)]
			}

	# Recur
	new_next_page_tok = api_results["nextPageToken"] if "nextPageToken" in api_results else ''
	return get_comment_threads(vid_id, data, new_next_page_tok)


def get_comments(vid_id, data=None, next_page_tok=None):
	""" Get the thread of comments from a videoID """

	def comments_list(parent_id):
		"""Get the comments from a particular thread"""
		api_results = youtube.comments().list(
			part 		= "snippet",
			parentId 	= parent_id,
			textFormat 	= "plainText",
		).execute()
		comments = api_results["items"]
		return comments

	def format_comment(comment):
		""" Format comments """
		return {
			'author': comment["snippet"]["authorDisplayName"],
			'date'	: comment["snippet"]["updatedAt"],
			'text'	: comment["snippet"]["textDisplay"]
		}
	#######################################################
	next_page_tok = None
	data =[]
	while next_page_tok != '':
		# Get the thread via API call
		api_results = youtube.commentThreads().list(
			part 		= "snippet",
			videoId 	= vid_id,
			textFormat	= "plainText",
			maxResults	= 100,
			pageToken 	= next_page_tok
		).execute()

		# Process the thread and get the associated comments
		for item in api_results["items"]:
			comment_id 	= item["id"]
			num_replies = item["snippet"]["totalReplyCount"]
			top_comment = format_comment(item["snippet"]["topLevelComment"])
			data.append(top_comment)
			if num_replies >= 1:
				for comment in comments_list(comment_id):
					new_comment = format_comment(comment) 
					data.append(new_comment)
		next_page_tok = api_results["nextPageToken"] if "nextPageToken" in api_results else ''
		next_page_tok = '' if next_page_tok is None else next_page_tok #condition for while loop sanity
		return data



def get_video_data(vid_id, categories_list, method_type='aprox'):
	""" Gets all the relevant data for a video """
	video_info_list = youtube.videos().list(
		part="topicDetails, snippet, contentDetails, statistics",
		id = vid_id
	).execute()

	video_info 	= video_info_list["items"][0]
	title 			= video_info["snippet"]["title"]
	duration_string = video_info["contentDetails"]["duration"]
	video_defintion = video_info["contentDetails"]["definition"]
	num_views 		= int(video_info["statistics"]["viewCount"])
	publish_date 	= video_info["snippet"]["publishedAt"]
	topics 			= video_info["topicDetails"]["topicIds"] if 'topicDetails' in video_info and 'topicIds' in video_info["topicDetails"] else [] #code around bug
	captions 		= get_formatted_transcript(vid_id)

	if num_views < 100000: #Optimization by doing this check also throws away videos with bad captions
		return None
	if captions == None: #Optimization by doing this check also throws away videos with bad captions
		return None
	vid_data = {
		"title" 				: title,
		"video_length" 			: duration_string,
		"video_defintion"		: video_defintion,
		"number_views" 			: num_views,
		"publish_date" 			: publish_date,
		"topics" 				: topics,
		'categories'			: categories_list,
		"captions" 				: captions,
	}
	if method_type=='aprox':
		raw_score 				= get_approx_score(vid_id) 
		vid_data['raw_score'] 	= raw_score
		vid_data['score']		= (raw_score/float(num_views))
	elif method_type=='threads':
		vid_data['comment_thread'] = get_comment_threads(vid_id)
	else:
		vid_data['comments'] = get_comments(vid_id)

	return vid_data

def process_inv_idx(inv_idx, path=None, cautious=True):
	vid_id_set = set(get_filenames(path))
	all_data = {}
	for vid_id, categories_list in inv_idx.iteritems():
		if vid_id not in vid_id_set:
			print "proccessing: ", vid_id
			cur_vid_data = get_video_data(vid_id, categories_list, method_type="comments")
			if cautious:
				with open(path+vid_id+'.json', 'w') as datafile:
					json.dump(cur_vid_data, datafile, indent = 4, ensure_ascii=True)
			else:
				all_data[vid_id] = cur_vid_data
	return all_data



def try_forever(eval_string):
	try:
		eval(eval_string)
	except:
		try_forever(eval_string)


if __name__ == "__main__":
	os.chdir(r'C:\Users\Maheer\Dropbox\Cornell Course Materials\Spring 2015\CS 4300\youtube-caption-prediction\data') #go into data folder
	input_json_filename = 'video_ids_v9_p2_1.json'
	videoIds_inv_idx = json.load(open(input_json_filename))
	eval_string = 'process_inv_idx(videoIds_inv_idx, path="raw_comments_v2/", cautious=True)'
	try_forever(eval_string)

	# with open('video_ids_v5_pruned_pruned_data.json', 'w') as datafile:
	# 	json.dump(videos_data, datafile, indent = 4, ensure_ascii=True)