"""
This file constitutes a quick "sketch" of the library's API design so that I'm 
not making everything up entirely as I go. Once this library is actually 
implemented, this file should work (or be very close).
"""

import time
import datetime
import logging

import podstar
import slugify


def main():
	# Create a new Feed
	f = podstar.Feed("http://bit.ly/2qBYf0s")

	###
	# Get basic information about a feed.
	###

	print(f.title)
	print(f.description)

	###
	# Discover all episodes within the feed.
	###

	for episode in f.episodes():
		print("- {title} ({pub_date})".format(
			title=episode.title,
			pub_date=episode.published_at.strftime("%a %b %d, %Y")))
		
		duration = "unknown"
		if episode.soft_duration is not None:
			duration = time.strftime(
				"%H:%M:%S", time.gmtime(episode.soft_duration))
		
		print("  [{duration}] {audio_url}".format(
			duration=duration,
			audio_url=episode.audio.url))

	###
	# Download an episode matching a specific date.
	###

	target_date = datetime.date(2017, 2, 22)
	on_date = filter(lambda e: e.published_at.date() == target_date, f.episodes())

	for episode in on_date:
		filename = slugify.slugify(episode.title) + episode.audio.filename_ext
		
		print("Saving episode '{title}' to '{filename}'...".format(
			title=episode.title,
			filename=filename))

		with open(filename, 'wb+') as fh:
			episode.audio.save(fh)


if __name__ == '__main__':
	main()