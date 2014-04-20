=================
django-urlmonitor
=================

Just a signal receiver for handling changes to an object's URLs and inserting
HTTP redirects (via ``django.contrib.redirects``) when necessary.

Currently monitors for changes to ``get_absolute_url`` and ``get_list_url``

Set ``URLMONITOR_MODELS`` in your project's settings like so::

    URLMONITOR_MODELS = (
        'app.Model',
        'anotherapp.Model',
        'auth.User',
        ...  # and so on.
    )

and enable auto-registration based on that constant, probably in your root
urlconf or something::

    import urlmonitor; urlmonitor.autodiscover()

which will set up **pre-save** listeners for each given model.


Requirements
------------

* `Django`_
* ``django.contrib.redirects``
* ``django.contrib.sites``


License
-------

``django-urlmonitor`` is available under the terms of the
Simplified BSD License (alternatively known as the FreeBSD License, or
the 2-clause License). See the ``LICENSE`` file in the source
distribution for a complete copy.

.. _Django: https://djangoproject.com/
