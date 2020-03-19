from karma.sqlalchemy_declarative import Karma


def increment(session, subject, amount):
    # Retreive subject, add amount to karma value,
    #   create new subject with [amount] karma if necesary
    entry = session.query(Karma).filter(Karma.subject == subject).one_or_none()

    if entry is None:
        session.add(Karma(subject=subject, karma=amount))
    else:
        entry.karma = entry.karma + amount

    session.commit()


def decrement(session, subject, amount):
    # Retreive subject, subtract amount from karma value,
    #   create new subject with -[amount] karma if necesary
    return increment(session, subject, -amount)


def get_by_subject(session, subject):
    # Return subject and karma if found
    entry = session.query(Karma).filter(Karma.subject == subject).one_or_none()

    if entry is None:
        return None

    return entry.karma


def get_top(session, num_to_select):
    top_scores = session.query(Karma.karma).order_by(Karma.karma.desc()) \
        .distinct().limit(num_to_select)
    entries = session.query(Karma).filter(Karma.karma.in_(top_scores)) \
        .order_by(Karma.karma.desc())

    entry_dict = {}
    for entry in entries:
        entry_dict[entry.subject] = entry.karma

    return entry_dict
