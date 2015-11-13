#!/usr/bin/env python


import os.path
import datetime
from bluesky.datanaming import DataNaming


class TiffExporter(object):

    use_mtime = True
    mtime_window = 0.05
    default_fetch = 'pe1_image_lightfield'


    def __init__(self, fetch=None, template=None, prefix=None):
        self.fetch = self.default_fetch if fetch is None else fetch
        self.naming = DataNaming(template, prefix)
        return


    def __str__(self):
        "Human-readable configuration of this object."
        lines = ["TiffExporter() attributes",
                 "  fetch = {0.fetch}",
                 "  naming = {0.naming}",
                 "  use_mtime = {0.use_mtime}",
                 "  mtime_window = {0.mtime_window}",]
        rv = "\n".join(lines).format(self)
        return rv


    def __call__(self, h, select=None, dryrun=False, overwrite=False):
        """Export sequentially-numbered TIFF files from databroker header.

        Parameters
        ----------
        h : Header
            a header from the databroker
        select : array of integer indices or a slice object like numpy.s_[-3:]
            Save outputs only from the events at selected indices.
        dryrun : bool
            When True, display what would be done without taking
            any action.
        overwrite : bool
            Replace existing tiff files when True.

        No return value.
        """
        import tifffile
        from databroker import get_events
        if dryrun:
            dryordo = lambda msg, f, *args, **kwargs:  print(msg)
        else:
            dryordo = lambda msg, f, *args, **kwargs:  f(*args, **kwargs)
        setmtime = lambda f, t: os.utime(f, (os.path.getatime(f), t))
        noop = lambda : None
        msgrm = "remove existing output {}"
        msgskip = "skip {f} already saved as {o}"
        outputfiles = self.naming(h)
        eventtimes = [e.time for e in get_events(h, fill=False)]
        n = len(eventtimes)
        selection = _makesetofindices(n, select)
        dircache = {}
        outputfrom = {
                f : self.outputFileExists(f,
                    mtime=self.use_mtime and etime, dircache=dircache)
                for f, etime in zip(outputfiles, eventtimes)}
        imgs = self.fetch(h)
        for i, f, img, etime in zip(range(n), outputfiles, imgs, eventtimes):
            if not i in selection:  continue
            existingoutputs = outputfrom[f]
            # skip this image when overwrite is False
            if not overwrite:
                for o in existingoutputs:
                    print(msgskip.format(f=f, o=o))
                if existingoutputs:  continue
            assert overwrite or not existingoutputs
            for o in existingoutputs:
                dryordo(msgrm.format(o), os.remove, o)
            msg = "write image data to {}".format(f)
            dryordo(msg, tifffile.imsave, f, img)
            if self.use_mtime:
                isotime = datetime.datetime.fromtimestamp(etime).isoformat(' ')
                msg = "adjust image file mtime to {}".format(isotime)
                dryordo(msg, setmtime, f, etime)
        return


    def findExistingTiffs(self, h, select=None):
        """Return a list of already existing TIFF outputs for databroker
        header.

        Parameters
        ----------
        h : Header
            a header from the databroker
        select : array of integer indices or a slice object like numpy.s_[-3:]
            Find outputs only from the events at specified indices.
        """
        from databroker import get_events
        # avoid repeated calls to os.listdir
        dircache = {}
        filenames = self.naming(h)
        eventtimes = [e.time for e in get_events(h, fill=False)]
        if not self.use_mtime:
            eventtimes = len(eventtimes) * [None]
        n = len(eventtimes)
        selection = _makesetofindices(n, select)
        rv = []
        for i, f, etime in zip(range(n), filenames, eventtimes):
            if not i in selection:  continue
            rv.extend(self.outputFileExists(f, etime, dircache=dircache))
        return rv


    def outputFileExists(self, filename, mtime=None, dircache=None):
        """Check if there already are any existing tiff files.

        filename -- output filename to be checked
        mtime    -- file modification time in seconds or None.
                    When specified and nonzero, match tiff files in the
                    filename directory with mtime closer than mtime_window.

        Return a list of full paths of existing tiff files.
        """
        fa = os.path.abspath(filename)
        rv = [fa] if os.path.exists(filename) else []
        if not mtime:  return rv
        outputdir = os.path.abspath(os.path.dirname(filename))
        ext = os.path.splitext(filename)
        dircache = dircache if dircache is not None else {}
        if not outputdir in dircache:
            ofiles = [os.path.join(outputdir, f)
                    for f in os.listdir(outputdir)]
            ofiles = [f for f in ofiles
                    if f.endswith(ext) and os.path.isfile(f)]
            dircache[outputdir] = ofiles
        for f in dircache[outputdir]:
            if f == fa:
                assert rv[0] == f
                continue
            dt = abs(os.path.getmtime(f) - mtime)
            if dt < self.mtime_window:
                rv.append(f)
        return rv

    # Properties -------------------------------------------------------------

    @property
    def fetch(self):
        """Function that generates image arrays from a DataBroker headers.

        Must be a callable object or a string.  When set to a string NAME,
        use get_images(headers, NAME).
        """
        return self._fetch

    @fetch.setter
    def fetch(self, value):
        if isinstance(value, str):
            from functools import partial
            from databroker import get_images
            self._fetch = partial(get_images, name=value)
        elif callable(value):
            self._fetch = value
        else:
            emsg = "The fetch attribute must be a string or callable object."
            raise TypeError(emsg)
        return

# class TiffExporter


def _makesetofindices(n, select):
    import numpy
    indices = numpy.arange(n)
    if select is not None:
        indices = indices[select]
    return set(indices)
