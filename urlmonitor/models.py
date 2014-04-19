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

from django.db.models.signals import pre_save
from django.template.defaultfilters import slugify


logger = logging.getLogger(__name__)


def maybe_update_redirect(sender, instance, using, *args, **kwargs):
    """
    This is a function for connecting as a *pre_save* signal.

    :return: whether or not anything needed to change.
    :rtype: boolean
    """
    # unsaved previously
    if not instance.pk:
        return False

    # no configured URL to monitor
    if not hasattr(instance, 'get_absolute_url'):
        return False

    new_url = instance.get_absolute_url()
    previous_obj = sender._default_manager.using(using).get(pk=instance.pk)
    old_url = previous_obj.get_absolute_url()

    if new_url == old_url:
        return False

    # either update the existing redirect to point to the new url, or create
    # a new one - avoiding any further signals listening to Redirect
    manager = Redirect.objects.using(using)
    try:
        old_redirect = manager.get(old_path=old_url)
        manager.filter(pk=old_redirect.pk).update(new_path=new_url)
    except Redirect.DoesNotExist:
        manager.create(old_path=old_url, new_path=new_url,
                       site=Site.objects.get_current())

    # delete anything that has our *new* URL as its old path.
    manager.filter(old_path=new_url).delete()
    return True


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

    resolved_models = []
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
        else:
            resolved_models.append(real_model)

    resolved_models_count = len(resolved_models)
    if resolved_models_count < 1:
        logger.info("No model classes configured for URL monitoring")
        return None

    for model in resolved_models:
        model_slug = slugify(model._meta.verbose_name)
        uid = "urlmonitor_{0}".format(model_slug)
        pre_save.connect(receiver=maybe_update_redirect, sender=model,
                         dispatch_uid=uid)
        debug_msg_args = {'cls': model.__class__, 'uid': uid}
        debug_msg = ("pre_save signal connected to maybe_update_redirect for "
                     "{cls} using dispatch_uid={uid}")
        logger.debug(debug_msg.format(**debug_msg_args))  # noqa
    return resolved_models_count
