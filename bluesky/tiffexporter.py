#!/usr/bin/env python


import os.path
import datetime
import tifffile


class TiffExporter(object):

    set_mtime = True
    mtime_window = 0.05
    default_fetch = 'pe1_image_lightfield'


    def __init__(self, fetch=None, template=None, prefix=None):
        from .datanaming import DataNaming
        self.fetch = self.default_fetch if fetch is None else fetch
        self.naming = DataNaming(template, prefix)
        return


    def __str__(self):
        "Human-readable configuration of this object."
        lines = ["TiffExporter() configuration:",
                 "  fetch = {self.fetch}",
                 "  naming = {self.naming}",
                 "  set_mtime = {self.set_mtime}",
                 "  mtime_window = {self.mtime_window}",]
        rv = "\n".join(lines).format(self)
        return rv


    def __call__(self, h, dryrun=False, overwrite=False):
        """Export sequentially-numbered TIFF files from databroker header.

        Parameters
        ----------
        h : Header
            a header from the databroker
        dryrun : bool
            When True, display what would be done without taking
            any action.
        overwrite : bool
            Replace existing tiff files when True.

        No return value.
        """
        from databroker import get_events
        if dryrun:
            dryordo = lambda msg, f, *args, **kwargs:  print(msg)
        else:
            dryordo = lambda msg, f, *args, **kwargs:  f(*args, **kwargs)
        noop = lambda : None
        msgrm = "remove existing output {}"
        msgskip = "skip {f} as it is already saved as {o}"
        outputfiles = self.naming(h)
        imgs = self.fetch(h)
        events = get_events(h, fill=False)
        dircache = {}
        for f, img, e in zip(outputfiles, imgs, events):
            existingoutputs = self.outputFileExists(f, dircache=dircache)
            # skip this image when overwrite is False
            if not overwrite:
                for o in existingoutputs:
                    print(msgskip.format(f=f, o=o))
                continue
            assert overwrite
            for o in existingoutputs:
                dryordo(msgrm.format(o), os.remove, o)
            msg = "write image as {}".format(f)
            dryordo(msg, tifffile.imsave, f, img)
            if self.set_mtime:
                stinfo = os.stat(f)
                isotime = datetime.datetime.fromtimestamp(e.time).isoformat(' ')
                msg = "adjust mtime of {} to {}".format(f, isotime)
                dryordo(msg, os.utime, f, (stinfo.st_atime, event.time))
        return


    def findExistingTiffs(self, h):
        """Return a list of already existing TIFF outputs for databroker
        header.
        """
        from databroker import get_events
        # avoid repeated calls to os.listdir
        dircache = {}
        filenames = self.naming(h)
        events = get_events(h, fill=False)
        rv = []
        for f, e in zip(filenames, events):
            mtime = e.time if self.set_mtime else None
            rv.extend(self.outputFileExists(f, mtime, dircache=dircache))
        return rv


    def outputFileExists(self, filename, mtime=None, dircache=None):
        """Check if there already are any existing tiff files.

        filename -- output filename to be checked
        mtime    -- file modification time in seconds or None.
                    When specified, match tiff files in the
                    filename directory with the same mtime.

        Return a list of full paths of existing tiff files.
        """
        fa = os.path.abspath(filename)
        rv = [fa] if os.path.exists(filename) else []
        if mtime is None:  return rv
        outputdir = os.path.abspath(os.path.dirname(filename))
        ext = os.path.splitext
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
            if dt < self._mtime_window:
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
            self._fetch = partial(get_images, value)
        elif callable(value):
            self._fetch = value
        else:
            emsg = "fetch must be set to a string or callable object."
            raise TypeError(emsg)
        return

# class TiffExporter
