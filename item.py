import api
import item_model
import dao

def handle_item_operation(item_operation, gives_trigger, max_held_items, held_items, channel, message_data):
    operation = item_operation.group(1)
    item_name = item_operation.group(2) or item_operation.group(3)
    print("Got operation: \"" + operation + "\" and item: \"" + item_name + "\"")
    if (operation == gives_trigger):
        handle_give(item_name, held_items, max_held_items, channel, message_data)
    else:
        handle_take(item_name, held_items, channel, message_data)

def handle_give(item_name, held_items, max_held_items, channel, message_data):
    user_name = api.get_user_name(message_data['user'])
    channel_name = api.get_name_from_id(message_data['channel'])

    new_item = item_model.Item()
    new_item.new(item_name, user_name, channel_name)

    # If we're able to hold more items
    if (len(held_items) < max_held_items):
        dao.insert_item(new_item)
        response = ("_takes *" + item_name + "* from " + user_name + "_")
    else:
        # We can't hold any more items, so we'll have to hand an old one back
        old_item = dao.swap_items(new_item)
        held_items.remove(old_item.name)
        response = ("_takes *" + item_name + "* from " + user_name + " and hands them *" + old_item.name + "*_")

    held_items.append(item_name)

    print("new held_items: " + str(held_items))
    api.send_reply(response, channel)

def handle_take(item_name, held_items, channel, message_data):
    # If we're not holding the item requested
    if (item_name not in held_items):
        response = ("Sorry <@" + message_data['user'] + ">, I can't give you something that I don't have!")
    else:
        user_name = api.get_user_name(message_data['user'])
        channel_name = api.get_name_from_id(message_data['channel'])

        dao.delete_item_by_name(item_name)
        held_items.remove(item_name)

        response = ("_hands " + user_name + " *" + item_name + "*_")

    print("new held_items: " + str(held_items))
    api.send_reply(response, channel)

def list_items(held_items, channel):
    response = "I am currently holding "

    if (len(held_items) > 2):
        for item in held_items[:-1]:
            response += (item + ", ")
        response += " and " + held_items[-1]
    elif (len(held_items) == 2):
        response += held_items[0] + " and " + held_items[1]
    elif (len(held_items) == 1):
        response += held_items[0]
    else:
        response = "I'm not currently holding anything!"

    api.send_reply(response, channel)
