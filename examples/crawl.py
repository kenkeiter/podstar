import multiprocessing
import multiprocessing.dummy

import podstar


def slurp_feed(url):
    try:
        feed = podstar.Feed(url)
        return {
            'title': feed.title,
            'url': feed.url,
            'episode_count': sum((1 for episode in feed.episodes()))
        }
    except Exception as e:
        return e

def run(feed_count=100, pool_size=8, green_threads=True):
    try:
        base_url = "http://www.digitalpodcast.com/feeds/go_rss?feed_id="
        urls = (base_url + str(i) for i in range(70000, 70000 + feed_count))

        pool_module = multiprocessing.dummy if green_threads else multiprocessing
        pool = pool_module.Pool(pool_size)

        errors = []
        feeds = []

        for result in pool.imap_unordered(slurp_feed, urls):
            if isinstance(result, Exception):
                errors.append(result)
            else:
                print("- {title} [{episode_count} episodes] {url}".format(**result))
                feeds.append(result)
    finally:
        print("=============================================")
        print("{} feeds parsed successfully ({} episodes!)".format(
            len(feeds), sum((f['episode_count'] for f in feeds))))
        print("{} errors encountered".format(len(errors)))
        print("=============================================")


if __name__ == '__main__':
    run(600)