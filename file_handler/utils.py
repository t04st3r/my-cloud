from django.shortcuts import _get_queryset


def get_earliest_objects_or_none(klass, *args, **kwargs):
    """ Return the earliest model if exists else none """
    queryset = _get_queryset(klass)
    if not hasattr(queryset, 'get'):
        klass__name = klass.__name__ if isinstance(klass, type) else klass.__class__.__name__
        raise ValueError(
            "First argument to get_earliest_objects_or_none() must be a Model, Manager, "
            "or QuerySet, not '%s'." % klass__name
        )
    try:
        return queryset.filter(*args, *kwargs).earliest('id')
    except queryset.model.DoesNotExist:
        return None
