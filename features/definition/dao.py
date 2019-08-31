from definition.sqlalchemy_declarative import Definition, Blacklist, Ignore, WordUsage
from sqlalchemy.sql.expression import func

def get_definition_by_trigger(session, trigger):
    # retrieve definition entry by given trigger
    entry = session.query(Definition).filter(Definition.trigger == trigger).order_by(func.random()).first()

    return entry

def insert_definition(session, trigger, relation, response, user):
    new_def = Definition(trigger = trigger, relation = relation, response = response, user = user)

    session.add(new_def)
    session.commit()

def get_triggers(session):
    triggers = session.query(Definition.trigger)

    # extract values from 1-element tuples
    return [i[0] for i in triggers]

def check_trigger(session, trigger):
    return session.query(Definition).filter(Definition.trigger == trigger).first()

def check_blacklist(session, trigger):
    return session.query(Blacklist).filter(Blacklist.trigger == trigger).one_or_none()

def insert_blacklist(session, trigger, user):
    if check_blacklist(session, trigger):
        return

    new_blacklisted = Blacklist(trigger = trigger, user = user)

    session.add(new_blacklisted)
    session.commit()

def remove_blacklist(session, trigger):
    blacklisted = session.query(Blacklist).filter(Blacklist.trigger == trigger).one_or_none()

    if not blacklisted:
        return

    session.delete(blacklisted)
    session.commit()

def check_ignored(session, user):
    return session.query(Ignore).filter(Ignore.ignored_user_id == user).one_or_none()

def insert_ignored(session, user):
    if check_ignored(session, user):
        return

    new_ignore = Ignore(ignored_user_id = user)

    session.add(new_ignore)
    session.commit()

def remove_ignored(session, user):
    ignored = session.query(Ignore).filter(Ignore.ignored_user_id == user).one_or_none()

    if not ignored:
        return

    session.delete(ignored)
    session.commit()
