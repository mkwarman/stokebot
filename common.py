""" Stateless helper functions to be used wherever convenient """

import re
import api

TAG_CHECK = re.compile(r'(<(?:@|#)[^ ]+>)')

def to_upper_if_tag(text):
    """ Search for and convert tags to uppercase so Slack handles them correctly """
    search_result = TAG_CHECK.search(text)

    if search_result:
        tag = search_result.group(1)
        text = text.replace(tag, tag.upper())

    return text

def to_real_name_if_tag(text):
    """ Search for and replace tags with user's friendly name """
    search_result = TAG_CHECK.search(text)

    if search_result:
        tag = search_result.group(1)
        user_id = tag[2:-1].upper()
        name = api.get_user_real_name(user_id)
        if not name:
            name = tag.upper()
        text = text.replace(tag, name)

    return text

def to_first_name_if_tag(text):
    """ Search for and replace tags with user's first name """
    search_result = TAG_CHECK.search(text)

    if search_result:
        tag = search_result.group(1)
        user_id = tag[2:-1].upper()
        name = api.get_user_first_name(user_id)
        if name:
            text = text.replace(tag, name)
        else:
            print("api.get_user_first_name returned None, checking for real_name instead")
            text = to_real_name_if_tag(text).split(" ")[0]

    return text
