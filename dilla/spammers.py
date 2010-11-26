#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
from dilla import spamlib
from django.contrib.webdesign import lorem_ipsum
import logging
log = logging.getLogger('dilla')

@spamlib.global_handler('ManyToManyField')
def generic_manytomany(field):
    return random_fk(field, 5)

@spamlib.global_handler('CharField')
def random_chars(field):
    max_length = field.max_length
    suffix = ''
    #if field.unique:
        #suffix = self._uuid()
    words = lorem_ipsum.words(random.randint(2,3), common = False)
    value = "%s%s" % ( words, suffix )
    if max_length and len(value) > max_length:
        return value[max_length:]
    return value

@spamlib.global_handler('ForeignKey')
def random_fk(field, slice = None):
    Related = field.rel.to
    log.debug('Trying to find related object: %s' % Related)
    try:
        query = Related.objects.all().order_by('?')
        if field.rel.limit_choices_to:
            log.debug('Field %s has limited choices. Applying to query.' % field)
            query.filter(**field.rel.limit_choices_to)
        if slice:
            return query[:slice]
        return query[0]
    except IndexError, e:
        log.info('Could not find any related objects for %s' % field.name)
        return None
    except Exception, e:
        log.critical(str(e))

@spamlib.strict_handler('testapp.Book.title')
def set_title(field):
    return "The Satanic Bible"

@spamlib.global_handler('PositiveIntegerField')
def meaning_of_life(field):
    return 42

