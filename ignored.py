import api
import user_model
import dao

def handle_ignore(command, channel, message_data, ignored_users):
    user_name = command[7:]
    user_id = ""

    if user_name == "me":
        user_name = api.get_user_name(message_data['user'])
    elif user_name.startswith("<@"):
        user_id = user_name[2:-1].upper()
        user_name = api.get_user_name(user_id)

    if not user_id:
        user_id = api.get_user_id(user_name)

    channel_name = api.get_name_from_id(message_data['channel'])

    if not (user_id and user_name):
        api.send_reply("Sorry <@" + message_data['user'] + ">, I couldn't find user \"" + command[7:] + "\"", channel)
        return

    user_object = user_model.User()
    user_object.new(user_id, user_name, channel_name)

    reply = ("Ok <@" + message_data['user'] + ">, I will ignore " + ("you" if message_data['user'] == user_id else "<@" + user_name + ">") + " (except commands)")

    if user_id not in ignored_users:
        dao.insert_ignored_user(user_object)
        ignored_users.append(user_id)
    else:
        print("user already in ignored_users, ignoring...")

    api.send_reply(reply, channel)

    print("new ignored_users: " + str(ignored_users))

def handle_listen(command, channel, message_data, ignored_users):
    user_name = command[10:]
    user_id = ""

    if user_name == "me":
        user_name = api.get_user_name(message_data['user'])
    elif user_name.startswith("<@"):
        user_id = user_name[2:-1].upper()
        user_name = api.get_user_name(user_id)

    if not user_id:
        user_id = api.get_user_id(user_name)

    if not (user_id and user_name):
        api.send_reply("Sorry <@" + message_data['user'] + ">, I couldn't find user \"" + command[10:] + "\"", channel)
        return

    reply = ("Ok <@" + message_data['user'] + ">, I will listen to " + ("you" if message_data['user'] == user_id else "<@" + user_name + ">"))

    if user_id in ignored_users:
        dao.delete_ignored_by_user_id(user_id)
        ignored_users.remove(user_id)
    else:
        print("user not in ignored_users, ignoring...")

    api.send_reply(reply, channel)

    print("new ignored_users: " + str(ignored_users))
