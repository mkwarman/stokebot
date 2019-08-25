from quote.sqlalchemy_declarative import Quote
from sqlalchemy.sql.expression import func

def add_quote(session, author, quote):
    quote = Quote(author = author, quote = quote)

    session.add(quote)
    session.commit()

def get_quote_by_author(session, author):
    return session.query(Quote).filter(Quote.author == author).order_by(func.random()).first()

