# -*- coding: utf-8 -*-
from .models import register_requested_models, maybe_update_redirect

__version_info__ = '0.1.0'  # pragma: no cover
__version__ = '0.1.0'  # pragma: no cover
version = '0.1.0'  # pragma: no cover


def get_version():
    return '0.1.0'


# allow usage `import urlmonitor; urlmonitor.autodiscover()`
autodiscover = register_requested_models

__all__ = ['get_version', 'register_requested_models',
           'maybe_update_redirect', 'autodiscover']
