from dilla import spammer

@spammer.register('Book.title')
def do_something():
    return "The Satanic Bible"

