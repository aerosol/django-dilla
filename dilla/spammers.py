#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.webdesign import lorem_ipsum
from dilla import spam
import random
import os
import decimal
import logging
log = logging.getLogger('dilla')

dictionary = getattr(settings, 'DICTIONARY', "/usr/share/dict/words")
if os.path.exists(dictionary) and \
        not getattr(settings, 'DILLA_USE_LOREM_IPSUM', False):
    d = open(dictionary, "r").readlines()
    _random_words = \
            lambda n: " ".join([random.choice(d).lower().rstrip() \
            for i in range(n)])
    _random_paragraph = lambda: _random_words(30).capitalize()
    _random_paragraphs = lambda n: \
            ".\n".join([_random_paragraph() for i in range(n)])
else:
    _random_words = lorem_ipsum.words
    _random_paragraphs = lorem_ipsum.paragraphs


@spam.global_handler('CharField')
def random_words(field):
    max_length = field.max_length
    words = _random_words(3)
    if max_length and len(words) > max_length:
        return words[max_length:]
    return words


@spam.global_handler('TextField')
def random_text(field):
    return _random_paragraphs(4)


@spam.global_handler('IPAddressField')
def random_ip(field):
    return ".".join([str(random.randrange(0, 255)) for i in range(0, 4)])


@spam.global_handler('SlugField')
def random_slug(field):
    return random_words(field).replace(" ", "-")


@spam.global_handler('BooleanField')
def random_bool(field):
    return bool(random.randint(0, 1))


@spam.global_handler('EmailField')
def random_email(field):
    return "%s@%s.%s" % ( \
             _random_words(1),
             _random_words(1),
             random.choice(["com", "org", "net", "gov", "eu"])
             )


@spam.global_handler('IntegerField')
def random_int(field):
    return random.randint(-10000, 10000)


@spam.global_handler('DecimalField')
def random_decimal(field):
    return decimal.Decimal(str(random.random() + random.randint(1, 20)))


@spam.global_handler('PositiveIntegerField')
def random_posint(field):
    return random.randint(0, 10000)


@spam.global_handler('ForeignKey')
def random_fk(field, slice=None):
    Related = field.rel.to
    log.debug('Trying to find related object: %s' % Related)
    try:
        query = Related.objects.all().order_by('?')
        if field.rel.limit_choices_to:
            log.debug('Field %s has limited choices. \
                    Applying to query.' % field)
            query.filter(**field.rel.limit_choices_to)
        if slice:
            return query[:slice]
        return query[0]
    except IndexError, e:
        log.info('Could not find any related objects for %s' % field.name)
        return None
    except Exception, e:
        log.critical(str(e))


@spam.global_handler('ManyToManyField')
def random_manytomany(field):
    return random_fk(field, random.randint(1, 5))
