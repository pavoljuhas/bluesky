#!/usr/bin/env python


class DataNaming(object):

    """Build filenames from fields in databroker header.

    prefix   -- fixed path that is prepended to the generated name.
    template -- string template where curly brackets will
                be exanded according to Python format minilanguage.
                Template segments denoted with "<>" such as "<segment>"
                are silently omitted, when their template expansion fails.

    Template expressions are expanded with the following variable names:

    h        -- Header object from the databroker.
    e        -- Event object from the Header h.
    N        -- sequence number of the Event e.
    start    -- abbreviation for h.start
    stop     -- abbreviation for h.stop if it exists
    scan_id  -- abbreviation for h.start.scan_id
    """

    prefix = ''
    _template = 'scan{scan_id:05d}_{N:03d}<-T{e.data[cs700]:03.1f}>.tiff'

    def __init__(self, template=None, prefix=None):
        if template is not None:
            self.template = template
        if prefix is not None:
            self.prefix = prefix
        return


    def __call__(self, h):
        """Generate names from fields in databroker header h."""
        from dataportal import get_events
        tparts = self._split_template(self.template)
        td = dict(h=h, start=h.start, scan_id=h.start.scan_id)
        td['stop'] = getattr(h, 'stop', None)
        events = get_events(h, fill=False)
        rv = [self._makename(tparts, td)
                for td['N'], td['e'] in enumerate(events)]
        return rv


    def __repr__(self):
        s = "DataNaming(template={!r}, prefix={!r})"
        return s.format(self.template, self.prefix)


    @property
    def template(self):
        """Template for generating names from databroker fields.
        """
        return self._template

    @template.setter
    def template(self, value):
        self._validate_template(value)
        self._template = value
        return


    def _makename(self, tparts, td):
        import os.path
        nmparts = []
        for seg, isopt in tparts:
            try:
                s = seg.format(**td)
            except (AttributeError, KeyError):
                if not isopt:  raise
                s = ''
            nmparts.append(s)
        rv = ''.join(nmparts)
        rv = os.path.join(self.prefix, rv)
        return rv


    @staticmethod
    def _validate_template(t):
        "Raise ValueError for invalid template string."
        import re
        hasN = re.search(r'\{N\b', t)
        if not hasN:
            raise ValueError("template must include '{N}'")
        tfixed = re.sub('[{][^}]*[}]', '', t)
        cleft = tfixed.count('<')
        cright = tfixed.count('>')
        if cleft != cright:
            raise ValueError("Unbalanced segment markers '<', '>'")
        if re.search('<[^>]<|>[^<]*>', t):
            raise ValueError("Nested or misordered segment markers '<', '>'")
        return


    @staticmethod
    def _split_template(t):
        """Split template string at '<segment>' markers.

        Return a list of (segment, isoptional) pairs where isoptional
        flag marks up optional template components.
        """
        import re
        segments = [[]]
        barebrac = re.split(r'(\{[^}]*\})', t)
        isopt = False
        isbracket = False
        while barebrac:
            w = barebrac.pop(0)
            delim = '>' if isopt else '<'
            if isbracket or not delim in w:
                segments[-1].append(w)
                isbracket = not isbracket
                continue
            assert delim in w
            wb, we = w.split(delim, 1)
            segments[-1].append(wb)
            segments.append([])
            isopt = not isopt
            barebrac.insert(0, we)
            continue
        rv = []
        for i, seg in enumerate(segments):
            isopt = bool(i % 2)
            s = ''.join(seg)
            if s:  rv.append((s, isopt))
        return rv


# class DataNaming
