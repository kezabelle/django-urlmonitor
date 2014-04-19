# -*- coding: utf-8 -*-
from .models import register_requested_models, maybe_update_redirect

# allow usage `import urlmonitor; urlmonitor.autodiscover()`
autodiscover = register_requested_models
__all__ = ['register_requested_models', 'maybe_update_redirect', 'autodiscover']
