from .core import (CallbackBase, CallbackCounter, print_metadata, collector,
                   get_obj_fields, CollectThenCompute, LiveTable)
from .fitting import LiveFit

# deprecate callbacks moved to mpl_plotting ----------------------------------

def _deprecate_import_name(name):
    wmsg = ("bluesky.callbacks.{0} is deprecated.  "
            "Use bluesky.callbacks.mpl_plotting.{0} instead.").format(name)
    def f(*args, **kwargs):
        from warnings import warn
        warn(wmsg, DeprecationWarning)
        from . import mpl_plotting
        cls = getattr(mpl_plotting, name)
        return cls(*args, **kwargs)
    f.__name__ = name
    return f

LiveScatter = _deprecate_import_name("LiveScatter")
LivePlot = _deprecate_import_name("LivePlot")
LiveGrid = _deprecate_import_name("LiveGrid")
LiveFitPlot = _deprecate_import_name("LiveFitPlot")
LiveRaster = _deprecate_import_name("LiveRaster")
LiveMesh = _deprecate_import_name("LiveMesh")

# ----------------------------------------------------------------------------
