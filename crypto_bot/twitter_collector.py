
#
# statuses = api.GetUserTimeline(44196397, trim_user=True, since_id=1389797504103981057)
import twitter


class TwitterCollector:

    def __init__(self, config):
        self.consumer_key = config['consumer_key']
        self.consumer_secret = config['consumer_secret']
        self.access_token = config['access_token']
        self.access_token_secret = config['access_token_secret']
        self.users = [44196397]
        self.last = None

        self.api = twitter.Api(consumer_key=self.consumer_key,
                               consumer_secret=self.consumer_secret,
                               access_token_key=self.access_token,
                               access_token_secret=self.access_token_secret)


    def get_latest(self):

        statuses = self.api.GetUserTimeline(44196397, trim_user=True)


        print()

