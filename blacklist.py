import api
import blacklisted_model
import dao

def handle_blacklist(command, channel, message_data, blacklisted_words):
    if api.is_admin(message_data['user']):
        sub_command = command[10:]
        print("sub_command: " + sub_command)
        if sub_command.startswith("add"):
            # add to blacklist
            blacklist_add(sub_command[4:], channel, message_data, blacklisted_words)
        elif sub_command.startswith("get"):
            # read from blacklist
            blacklist_read(sub_command[4:], channel, message_data, blacklisted_words)
        elif sub_command.startswith("delete"):
            # delete from blacklist
            blacklist_delete(sub_command[7:], channel, message_data, blacklisted_words)
        elif sub_command.startswith("showall"):
            # show full blacklist
            blacklist_showall(channel, blacklisted_words)
        else:
            api.send_reply("Try \"backlist add\", \"backlist get\", \"backlist delete\", or \"blacklist showall\"", channel)

    else:
        api.send_reply("Sorry <@" +message_data['user'] + ">, only admins can edit the blacklist.", channel)

def blacklist_add(word, channel, message_data, blacklisted_words):
    print("in blacklist_add, word: " + word)

    # Instantiate blacklist object
    blacklisted_object = blacklisted_model.Blacklisted()

    user_name = api.get_user_name(message_data['user'])
    channel_name = api.get_name_from_id(message_data['channel'])

    blacklisted_object.new(word, user_name, channel_name)

    dao.insert_blacklisted(blacklisted_object)
    blacklisted_words.append(word)
    api.send_reply("Ok <@" + message_data['user'] + ">, I've added " + word + " to the blacklist", channel)

def blacklist_read(word, channel, message_data, blacklisted_words):
    blacklisted = dao.get_blacklisted_by_word(word)

    print(blacklisted)
    api.send_reply(str(blacklisted), channel)

def blacklist_delete(blacklisted_id, channel, message_data, blacklisted_words):
    blacklisted = dao.get_blacklisted_by_id(blacklisted_id)
    if not blacklisted:
        api.send_reply("ID " + blacklisted_id + " does not exist.", channel)
        return
    dao.delete_blacklisted_by_id(blacklisted_id)
    blacklisted_words.remove(blacklisted.word)

    api.send_reply("Ok <@" + message_data['user'] + ">, I've removed " + blacklisted.word + " from the blacklist", channel)

def blacklist_showall(channel, blacklisted_words):
    blacklist = dao.select_all_blacklisted()

    for blacklisted in blacklist:
        print(str(blacklisted))
        api.send_reply(str(blacklisted), channel)
