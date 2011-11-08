#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf import settings
from django.db.models import get_app, get_models, get_model
from django.db import transaction
import random
import logging
import traceback

log = logging.getLogger(__name__)

__author__ = "Adam Rutkowski <adam@mtod.org>"
__contributors = """
Adolfo Fitoria (https://github.com/fitoria)
Rob Berry (https://github.com/rob-b)
Rafal Galczynski (https://github.com/rgsoda)
Alfredo Aguirre (https://github.com/alfredo/)
Philip Kalinsky (https://github.com/psychotechnik)
Mark Lavin (https://github.com/mlavin)
"""
__version__ = "0.2beta"


class AbstractRecord(object):
    """The class provides a little abstraction layer over either \
    a Django application, database model or specific database field.
    """

    def __init__(self, app, model=None, field=None):
        self.app = app
        self.model = model
        self.field = field
        self.many_to_many = False
        self.obj = None

    def is_app(self):
        return not self.model and not self.field

    def is_model(self):
        return self.model and not self.field

    def is_field(self):
        return self.model and self.field

    def create_object(self):
        assert self.model is not None
        Klass = self.model
        self.obj = Klass()
        return self.obj

    def set_object_property(self, value):
        assert self.obj and self.is_field()
        if self.many_to_many and self.obj and self.field.name and value:
            manager = getattr(self.obj, self.field.name)
            manager.add(*value)
        if self.obj and self.field.name and value:
            setattr(self.obj, self.field.name, value)
        return self.obj

    def save(self):
        self.obj.save()

    def __repr__(self):
        if self.is_app():
            return self.app
        if self.is_model():
            return "%s.%s" % (self.app, self.model.__name__)
        if self.is_field():
            return "%s.%s.%s" % (self.app, \
                    self.model.__name__, self.field.name)

    def __str__(self):
        return self.__repr__()

    def __unicode__(self):
        return self.__repr__()


class SpamRegistry(object):
    """Container storing spamming function references.
    Strict handlers are functions being directly intended to provide
    random data for one specific field.
    Global handlers provide random data to all fields of specific
    internal type.

    Every handler function should accept ``field`` argument.
    This is in fact an instance of any object derived from
    django.db.models.fields.Field

    Every handler function should return value applicable for the input field,
    with respect to django.db.Model attribute setting interface.

    NOTE:

        ManyToMany handlers should return values that are valid for
        django.db.models.fields.related.ManyRelatedManager.add()

    Example usage:

        from dilla import spam
        import string
        import random

        @spam.global_handler('CharField') # field.get_internal_type()
        def get_chars(field):
            return random.choice(string.ascii_letters)

        @spam.strict_handler('blog.Post.title')
        def get_blog_post_title(field):
            return random.choice(string.ascii_letters)
    """

    def __init__(self):
        self.global_handlers = {}
        self.strict_handlers = {}

    def _decorate(self, key, attr):
        def fn(f):
            attr.update({key: f})
            return f
        return fn

    def strict_handler(self, field_qname):
        return self._decorate(field_qname, self.strict_handlers)

    def global_handler(self, field_type):
        return self._decorate(field_type, self.global_handlers)

    def get_handler(self, record, strict=False):
        if strict:
            return self.strict_handlers.get(str(record), None)
        return self.strict_handlers.get(str(record), None) or \
                self.global_handlers.get(record.field.get_internal_type(), \
                None)

    def __repr__(self):
        return """strict_handlers: %s \nglobal handlers: %s""" % \
                (self.strict_handlers, self.global_handlers)

    def __str__(self):
        return self.__repr__()

spam = SpamRegistry()


class Dilla(object):
    """
    Dilla is a multi-purpose general testing tool for automated
    database spamming, intented to use with projects built on top of Django,
    populating data within any number of internal applications.

    Django SETTINGS used by Dilla class:

        DILLA_APPS = []           # Required, pretty much self-explanatory
                                  # Example value: ['blog', 'auth']
        DILLA_SPAMLIBS = []       # Optional list of user defined field
                                  # handlers to import.
                                  # See dilla.SpamRegistry
                                  # Example value:
                                  #       'blog.custom_blog_spammers']
        DILLA_EXCLUDE_MODELS = [] # Optional list of models to omit
                                  # Example value: ['blog.comment']

    One cycle of Dilla run means discovering all the application(s) models
    and saving database data generated by spamlibs.
    Default spamlib is bundled with Dilla under dilla.spammers and covers
    most of Django model fields. Development goal is to cover all of them.
    """

    def __init__(self, apps=None, cycles=1, \
            use_coin=True, spamlibs=None, single_transaction=True):
        if spamlibs is None:
            spamlibs = getattr(settings, 'DILLA_SPAMLIBS', [])
        spamlibs.insert(0, 'dilla.spammers')
        for lib in spamlibs:
            log.debug('Importing spamlib %s' % lib)
            self._dyn_import(lib)

        app_list = apps or getattr(settings, 'DILLA_APPS', None)
        assert app_list is not None, \
        "Either you have not provided Dilla.apps \
        parameter or settings.DILLA_APPS \
        is missing"
        self.spam_registry = spam
        self.apps = app_list
        self.cycles = cycles
        self.use_coin = use_coin
        self.appmodels = {}
        self.current = None
        self.rows_affected = 0
        self.fields_spammed = 0
        self.fields_omitted = 0

    def discover_models(self):
        apps = [(app, get_app(app)) for app in self.apps]
        for app_name, app_module in apps:
            self.appmodels[app_name] = []
            models = get_models(app_module)
            models_to_exclude = getattr(settings, 'DILLA_EXCLUDE_MODELS', None)
            if models_to_exclude:
                for excluded_model in models_to_exclude:
                    try:
                        models.remove(get_model(*excluded_model.split('.')))
                    except ValueError:
                            pass
            self.appmodels[app_name].extend(models)
        log.debug('Preparing to spam following models: %s' % self.appmodels)

    def find_spam_handler(self, record):
        strict_handler = self.spam_registry.get_handler(record, strict=True)
        if strict_handler:
            return strict_handler

        # if there's no strict handler defined for a choice field,
        # use generic random

        if record.field.choices:
            # If it's an instance of itertools.tee, which django does
            # if field._choices is a generator, then we can't take a
            # random choice without first converting choices to a list.
            choices = [c for c in record.field.choices]
            return lambda x, y: random.choice(choices)[0]

        return self.spam_registry.get_handler(record, strict=False)

    def spam(self, record):
        """This is where the magic happens and AbstractRecords evolve."""

        log.debug('[ --> Spam %s ]' % record)
        self.current = record

        if record.is_app():
            for model in self.appmodels.get(str(record)):
                record.model = model
                record.create_object()
                record.field = None
                self.spam(record)

        elif record.is_model():
            for field in [field for field \
                in record.model._meta.fields \
                if not field.auto_created]:

                record.many_to_many = False
                record.field = field
                self.spam(record)
            record.save()
            self.rows_affected += 1

            # after the record is saved, it is safe to fill
            # ManyToMany fields if any

            for field in record.model._meta.many_to_many:
                record.field = field
                record.many_to_many = True
                self.spam(record)

        elif record.is_field():
            if record.field.blank and (self.use_coin and self._coin_toss()):
                self.fields_omitted += 1
                log.debug("Using coin -- simon says, skip this record.")
                return

            handler = self.find_spam_handler(record)
            if handler is not None:
                value = handler(record, record.field)
                if record.field.unique:
                    manager = record.model._default_manager

                    # handlers may not return random values,
                    # try 5 times before giving up

                    for i in range(5):
                        try:
                            _match = manager.get(**{record.field.name: value})
                            value = handler(record, record.field)
                        except record.model.DoesNotExist, e:
                            break

                record.set_object_property(value)
                self.fields_spammed += 1
            else:
                log.warn("Handler not found for %s" % record)

    @transaction.commit_manually
    def run(self):
        try:
            self.discover_models()

            for cycle in range(self.cycles):
                log.info("spamming cycle: %d/%d" % (cycle + 1, self.cycles))
                for app in self.appmodels.keys():
                    self.spam(AbstractRecord(app))
            transaction.commit()
            return (len(self.apps),
                     self.rows_affected,
                     self.fields_spammed,
                     self.fields_omitted)

        except Exception, e:
            log.critical("%s" % e)
            transaction.rollback()
            raise

    def _dyn_import(self, name):
        mod, spamlib = name.rsplit('.', 1)
        m = __import__(mod, fromlist=[spamlib])
        return getattr(m, spamlib)

    def _coin_toss(self):
        return bool(random.randrange(2))
