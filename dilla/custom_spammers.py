#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dilla import spam

@spam.strict_handler('testapp.Book.isbn')
def get_isbn(field):
    return 42
