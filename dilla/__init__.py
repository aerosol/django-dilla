#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf import settings
from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_app, get_models
from django.contrib.webdesign import lorem_ipsum
from django.db import transaction, IntegrityError
import random
import string
import decimal
import sys
import logging
import datetime
import uuid

log = logging.getLogger(__name__)

class AbstractRecord(object):

    def __init__(self, app, model = None, field = None):
        self.app = app
        self.model = model
        self.field = field
        self.manytomany = False

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
        if self.manytomany:
            manager = getattr(self.obj, self.field.name)
            manager.add(*value)
        setattr(self.obj, self.field.name, value)
        return self.obj

    def save(self):
        self.obj.save()

    def __repr__(self):
        if self.is_app(): return self.app
        if self.is_model(): return "%s.%s" % (self.app, self.model.__name__)
        if self.is_field(): return "%s.%s.%s" % (self.app, self.model.__name__, self.field.name)

    def __str__(self):
        return self.__repr__()

    def __unicode__(self):
        return self.__repr__()


class SpamRegistry(object):

    def __init__(self):
        self.global_handlers = {}
        self.strict_handlers = {}

    def _decorate(self, key, attr):
        def fn(f):
            attr.update( { key : f } )
            return f
        return fn

    def strict_handler(self, field_qname):
        return self._decorate(field_qname, self.strict_handlers)

    def global_handler(self, field_type):
        return self._decorate(field_type, self.global_handlers)

    def get_handler(self, record, strict = False):
        if strict:
            return self.strict_handlers.get (str(record), None)
        return self.strict_handlers.get(str(record), None) or \
                self.global_handlers.get(record.field.get_internal_type(), None)

    def __repr__(self):
        return """strict_handlers: %s \nglobal handlers: %s""" % \
                (self.strict_handlers, self.global_handlers)

    def __str__(self):
        return self.__repr__()

spamlib = SpamRegistry()

class Dilla(object):

    def __init__(self, apps = None, cycles = 1, use_coin = True, spamlib = None):
        # TODO dynamic imports
        from dilla import spammers
        app_list = apps or getattr(settings, 'DILLA_APPS', None)
        assert app_list is not None, \
        "Either you have not provided Dilla.apps parameter or settings.DILLA_APPS \
is missing"
        self.apps = app_list
        self.cycles = cycles
        self.use_coin = use_coin
        self.appmodels = {}
        self.spamlib = spamlib

    def discover_models(self):
        apps = [(app, get_app(app)) for app in self.apps]
        for app_name, app_module in apps:
            self.appmodels[app_name] = []
            self.appmodels[app_name].extend(get_models(app_module))
        log.debug('self.appmodels: %s' % self.appmodels)

    def find_spam_handler(self, record):
        strict_handler = self.spamlib.get_handler(record, strict = True)
        if strict_handler:
            return strict_handler

        # if there's no strict handler defined for a choice field,
        # use generic random
        if record.field.choices:
            return lambda x: random.choice (x.choices)[0]

        return self.spamlib.get_handler(record, strict = False)

    def spam(self, record):
        log.debug('[ --> Spam %s ]' % record)

        if record.is_app():
            for model in self.appmodels.get( str(record) ):
                record.model = model
                record.create_object()
                record.field = None
                self.spam(record)

        elif record.is_model():
            for field in [field for field \
                    in record.model._meta.fields \
                    if not field.auto_created]:

                record.manytomany = False
                record.field = field
                self.spam(record)
            record.save()

            # after the record is saved, it is safe to fill
            # ManyToMany fields if any

            for field in record.model._meta.many_to_many:
                record.field = field
                record.manytomany = True
                self.spam(record)

        elif record.is_field():
            if record.field.blank and (self.use_coin and self._coin_toss()):
                log.debug("Using coin -- simon says, skip this record.")
                return

            handler = self.find_spam_handler(record)
            if handler is not None:
                record.set_object_property( handler(record.field) )
            else:
                log.warn("Handler not found for %s" % record)

    @transaction.commit_manually
    def run(self):
        try:
            self.discover_models()
            for app in self.appmodels.keys():
                self.spam(AbstractRecord(app))
            transaction.commit()
        except Exception, e:
            log.critical("%s" % e)
            log.critical(sys.exc_info())
            transaction.rollback()

    def _coin_toss(self):
        return bool(random.randrange(2))


