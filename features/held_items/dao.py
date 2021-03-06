from held_items.sqlalchemy_declarative import Item


def get_item_count(session):
    return session.query(Item).count()


def swap_items(session, name, username):
    oldest_item = session.query(Item).order_by(Item.date_time_added.asc()) \
            .first()

    session.delete(oldest_item)
    session.add(Item(name=name, username=username))
    session.commit()

    return oldest_item.name


def insert_item(session, name, username):
    item = Item(name=name, username=username)

    session.add(item)
    session.commit()


def get_held_items(session):
    items = session.query(Item.name).order_by(Item.date_time_added.asc())

    # extract values from 1-element tuples
    return [i[0] for i in items]
