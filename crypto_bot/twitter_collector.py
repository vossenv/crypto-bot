import twitter


class TwitterCollector:

    def __init__(self, config):
        self.consumer_key = config['consumer_key']
        self.consumer_secret = config['consumer_secret']
        self.access_token = config['access_token']
        self.access_token_secret = config['access_token_secret']
        self.update_rate = config['update_rate']

        self.api = twitter.Api(consumer_key=self.consumer_key,
                               consumer_secret=self.consumer_secret,
                               access_token_key=self.access_token,
                               access_token_secret=self.access_token_secret)

    def get_latest(self, user, last):
        count = 1 if not last else None
        return self.api.GetUserTimeline(screen_name=user, since_id=last, count=count)
