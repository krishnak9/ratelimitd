"""
Custom Policy Implementation
"""
from Logger import Logger
from ProfileLookup import ProfileLookup
from RedisConn import RedisConn


class SenderDomainBasedSenderPolicy:
    """
    This class provides Sender Domain based sender rate limiting
    """
    # Sender's domain based  
    key = 'sender'
    prefix = 'SDomainB_SenderPolicy_'
    quota = {}

    def __init__(self, parsed_config):
        self.parsed_config = parsed_config
        self.Enforce = parsed_config.getboolean('SenderDomainBasedSenderPolicy', 'Enforce')
        self.RejectMessage = parsed_config.get('SenderDomainBasedSenderPolicy', 'RejectMessage')
        self.ProfileLookupObj = ProfileLookup.create_profile_lookup('SenderDomainBasedSenderPolicy', parsed_config)
        self.ProfileCacheTTL = parsed_config.getint('SenderDomainBasedSenderPolicy', 'ProfileCacheTime')
        for i in parsed_config.items('SenderDomainBasedSenderPolicy-Profiles'):
            rates = i[1].split(',')
            limits = []
            for rate in rates:
                limits.append(rate.split('/'))
            profile = i[0].lower()
            SenderDomainBasedSenderPolicy.quota[profile] = []#(int(limits[0]), int(limits[1]))
            for limit in limits:
                mails = int(limit[0])
                time = int(limit[1])
                SenderDomainBasedSenderPolicy.quota[profile].append([mails,time])
        self.value = self.profile = self.error = None
#implementation left
    def check_quota(self, message, redis_pipe):
        self.value = message.data[self.key].lower()
        self.error = False
        if self.value != '':

            # policy will be applicable to each sender
            # profiles will be based on sender domain instead of sender itself
             
            self.profile = self.ProfileLookupObj.lookup(self.value.split('@')[1].lower(), self.ProfileCacheTTL)
            object_keys = []
            object_args = []
            no_of_limits = len(SenderDomainBasedSenderPolicy.quota[self.profile])
            for l_no in range(0,no_of_limits):
                object_keys.append(SenderDomainBasedSenderPolicy.prefix + self.value + "_" + str(l_no))
                object_args.append(SenderDomainBasedSenderPolicy.quota[self.profile][l_no][0])
            RedisConn.LUA_CALL_CHECK_LIMIT_MULTIPLE(keys=object_keys,
                                           args=object_args, client=redis_pipe)
        else:
            self.error = True
            RedisConn.LUA_CALL_DO_NOTHING_SLAVE(keys=[], args=[], client=redis_pipe)

    def update_quota(self, redis_pipe):
        if self.error:
            RedisConn.LUA_CALL_DO_NOTHING_MASTER(keys=[], args=[], client=redis_pipe)
        else:
            object_keys = []
            object_args = []
            no_of_limits = len(SenderDomainBasedSenderPolicy.quota[self.profile])
            for l_no in range(0,no_of_limits):
                object_keys.append(SenderDomainBasedSenderPolicy.prefix + self.value + "_" + str(l_no))
                object_args.append(SenderDomainBasedSenderPolicy.quota[self.profile][l_no][1]) 
            RedisConn.LUA_CALL_INCR_MULTIPLE(keys=object_keys,
                                    args=object_args, client=redis_pipe)

    def log_quota(self, accept, redis_val=None):
        if accept:
            if self.error:
                Logger.log('SenderDomainBasedSenderPolicy Sender: NullSender Action: accept')
            else:
                Logger.log('SenderDomainBasedSenderPolicy Sender: %s Quota: %s Profile: %s Action: accept' % (
                    self.value, self.create_log_data(redis_val) , self.profile))
        else:
            Logger.log(
                'SenderDomainBasedSenderPolicy Sender: %s Quota: Exceeded Profile: %s Action: reject' % (self.value, self.profile))

    def create_log_data(self, redis_val=None):
        # function to create log messages if we have multiple limits
        limits = SenderDomainBasedSenderPolicy.quota[self.profile]
        current_values = list(redis_val)
        limits_len = len(current_values)
        log_string = ""
        for i in range(0,limits_len):
            log_string = log_string + " limit (%s/%s) " % (redis_val[i],limits[i][0])
        return log_string               