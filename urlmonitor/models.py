# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
from django.conf import settings
from django.contrib.redirects.models import Redirect
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured

try:
    from django.apps import apps
    get_model = apps.get_model
except ImportError:  # pragma: no cover ... Django < 1.7
    from django.db.models.loading import get_model

try:
    from celery import shared_task
except ImportError:
    def shared_task(func):
        func.delay = func
        return func

from django.db.models.signals import pre_save
from django.template.defaultfilters import slugify
from .utils import hasattrs, maybecallattr


logger = logging.getLogger(__name__)
attrs_to_check = (
    'get_absolute_url',
    'get_list_url',
)


def maybe_update_redirect(sender, instance, using, *args, **kwargs):
    """
    This is a function for connecting as a *pre_save* signal.

    :return: whether or not anything needed to change.
    :rtype: boolean
    """
    # unsaved previously
    if not instance.pk:
        return False

    valid_attrs_to_check = hasattrs(instance, *attrs_to_check)
    # this pre-check allows us to fail early without asking the DB for the
    # old instance.
    if not valid_attrs_to_check:
        return False

    # we now know it's worth getting the old instance from the DB.
    try:
        previous_obj = sender._default_manager.using(using).get(pk=instance.pk)
    except sender.DoesNotExist:
        msg = ("Unable to get previous instance, even though there was an "
               "allegedly correct primary key: {}".format(instance.pk))
        logger.error(msg, exc_info=1)
        return False

    a_url_changed = False

    # we know we'll have at least one URL to compare and handle.
    for attrib in valid_attrs_to_check:
        new_url = maybecallattr(instance, attrib)
        old_url = maybecallattr(previous_obj, attrib)

        # make sure both sides aren't stupid
        if not all((old_url, new_url)):
            continue

        # they're the same, so skip doing anything else in this iteration.
        if new_url == old_url:
            continue

        a_url_changed = True
        site_id = Site.objects.get_current().pk

        # this may fire via celery, or immeidiately, depending on if
        # celery is installed.
        # We pass the site id through on the offchance the celery instance
        # is not using the same site_id as the signal which triggered
        # the call.
        update_redirect.delay(old_url=old_url, new_url=new_url, using=using,
                              site_id=site_id)
    return a_url_changed


@shared_task
def update_redirect(using, old_url, new_url, site_id):
    """
    either update the existing redirect to point to the new url, or
    create a new one - avoiding any further signals listening to Redirect
    """
    manager = Redirect.objects.using(using)

    # delete anything that has our *new* URL as its old path.
    manager.filter(old_path=new_url, site_id=site_id).delete()

    try:
        # ask for any old redirect that exists for the old url
        old_redirect = manager.get(old_path=old_url, site_id=site_id)
    except Redirect.DoesNotExist:
        # there was no previous redirect, and the URLs aren't the same,
        # so we'll create one.
        return manager.create(old_path=old_url, new_path=new_url,
                              site_id=site_id)

    # there was a previous redirect instance, so update it.
    # also we shouldn't need to filter by the site here, because there
    # won't be multiple sites using the same pks.
    return manager.filter(pk=old_redirect.pk).update(new_path=new_url)


class URLMonitorConfigError(ImproperlyConfigured):
    pass


def register_requested_models(configured_models=None):
    if 'django.contrib.redirects' not in settings.INSTALLED_APPS:
        raise URLMonitorConfigError(
            "`django.contrib.redirects` must be present in your "
            "INSTALLED_APPS to make use of the `urlmonitor` package.")

    if 'django.contrib.sites' not in settings.INSTALLED_APPS:
        raise URLMonitorConfigError(
            "`django.contrib.sites` must be present in your "
            "INSTALLED_APPS to make use of the `urlmonitor` package.")

    if configured_models is None:
        configured_models = getattr(settings, 'URLMONITOR_MODELS', ())

    configured_models_count = len(configured_models)
    if configured_models_count < 1:
        logger.info("No model strings configured for URL monitoring")
        return None

    resolved_models = set()
    for index, model in enumerate(configured_models):
        app, modelname = model.split('.', maxsplit=1)
        try:
            real_model = get_model(app_label=app, model_name=modelname)
        except LookupError:
            msg_args = {'index': index, 'count': configured_models_count,
                        'model': model}
            msg = ("Unable to find requested model {model} while iterating "
                   "over {count} configured items; check your "
                   "URLMONITOR_MODELS[{index}] for errors.")
            logger.exception(msg.format(**msg_args))
            real_model = None

        if real_model is not None and real_model not in resolved_models:
            resolved_models.add(real_model)
            model_slug = slugify(real_model._meta.verbose_name)
            uid = "urlmonitor_{0}".format(model_slug)
            pre_save.connect(receiver=maybe_update_redirect,
                             sender=real_model, dispatch_uid=uid)
            debug_msg_args = {'cls': model.__class__, 'uid': uid}
            debug_msg = ("pre_save signal connected to "
                         "maybe_update_redirect for {cls} using "
                         "dispatch_uid={uid}")
            logger.debug(debug_msg.format(**debug_msg_args))

    resolved_models_count = len(resolved_models)
    if resolved_models_count < 1:
        logger.info("No model classes configured for URL monitoring")
        return None
    return resolved_models_count
