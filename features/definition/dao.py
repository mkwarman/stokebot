from definition.sqlalchemy_declarative import Definition, Blacklist, Ignore, WordUsage

def get_by_trigger(session, trigger):
    # retrieve definition entry by given trigger
    entries = session.query(Definition).filter(Definition.trigger == trigger)

    return entries

def insert_definition(session, trigger, relation, response, user):
    new_def = Definition(trigger = trigger, relation = relation, response = response, user = user)

    session.add(new_def)
    session.commit()

def get_triggers(session):
    triggers = session.query(Definition.trigger)

    # extract values from 1-element tuples
    return [i[0] for i in triggers]
