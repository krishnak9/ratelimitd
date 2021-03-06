"""
Copyright 2015 Sai Gopal

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from urlparse import urlparse

from Logger import Logger


class ProfileLookup:
    """
    This class is an responsible for setting up profile lookups and interacting with them
    """

    @staticmethod
    def create_profile_lookup(policy, parsed_config):
        lookup_type = parsed_config.get(policy, 'ProfileLookupMethod')
        if lookup_type == 'None':
            Logger.log('Selected Lookup %s for Policy %s' % ('None', policy))
            from ProfileLookups.DefaultLookup import DefaultLookup
            return DefaultLookup()
        else:
            parsed_lookup_type = urlparse(lookup_type)
            if parsed_lookup_type.scheme == 'http' or parsed_lookup_type.scheme == 'https':
                Logger.log('Selected Lookup %s for Policy %s' % ('HTTP', policy))
                from ProfileLookups.HTTPLookup import HTTPLookup
                return HTTPLookup(parsed_lookup_type.geturl())
            elif parsed_lookup_type.scheme == 'hash':
                Logger.log('Selected Lookup %s for Policy %s' % ('Hash', policy))
                from ProfileLookups.HashLookup import HashLookup
                return HashLookup(parsed_lookup_type.path)
            elif parsed_lookup_type.scheme == 'postgresql':
                Logger.log('Selected Lookup %s for Policy %s' % ('postgresql', policy))
                from ProfileLookups.PSqlLookup import PSqlLookup
                return PSqlLookup(parsed_lookup_type.geturl(), parsed_config.get(policy, 'ProfileLookupQuery'))
            else:
                Logger.log('Unknown lookup type: %s' % lookup_type)
                Logger.log('Server Shutting Down')
                exit(1)

    def __init__(self):
        """
        Constructor
        """
