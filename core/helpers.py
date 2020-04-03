def get_text(data):
    if 'text' in data:
        return data['text']
    return None


def get_user_from_data(data):
    if ('user' in data):
        return data['user']

    return None
