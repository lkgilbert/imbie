from .collection import Collection
from imbie2.model.series import MassChangeDataSeries
from imbie2.util.combine import weighted_combine as ts_combine
from imbie2.util.sum_series import sum_series
import imbie2.model as model
from imbie2.const.error_methods import ErrorMethod
from imbie2.const.lsq_methods import LSQMethod

from typing import Iterator
import numpy as np
from scipy.io import savemat


class MassChangeCollection(Collection):
    def __iter__(self) -> Iterator[MassChangeDataSeries]:
        return super().__iter__()

    def combine(self) -> MassChangeDataSeries:
        if not self.series:
            return None
        elif len(self.series) == 1:
            return self.series[0]

        b_id = self.series[0].basin_id
        b_gp = self.series[0].basin_group
        b_a = self.series[0].basin_area

        u_gp = self.series[0].user_group
        d_gp = self.series[0].data_group

        for series in self:
            if series.basin_id != b_id:
                b_id = None
            if series.basin_group != b_gp:
                b_gp = None
            if series.basin_area != b_a:
                b_a = None
            if series.user_group != u_gp:
                u_gp = None
            if series.data_group != d_gp:
                d_gp = None

        ts = [series.t for series in self.series]
        ms = [series.mass for series in self.series]
        es = [series.errs for series in self.series]

        t, m = ts_combine(ts, ms)
        _, e = ts_combine(ts, es, error=True)

        return MassChangeDataSeries(None, u_gp, d_gp, b_gp, b_id, b_a, t, None, m, e)

    def average(self, mode=None) -> MassChangeDataSeries:
        raise NotImplementedError()

        if not self.series:
            return None
        elif len(self.series) == 1:
            return self.series[0]

        b_id = self.series[0].basin_id
        b_gp = self.series[0].basin_group
        b_a = self.series[0].basin_area

        u_gp = self.series[0].user_group
        d_gp = self.series[0].data_group

        for series in self:
            if series.basin_id != b_id:
                b_id = None
            if series.basin_group != b_gp:
                b_gp = None
            if series.basin_area != b_a:
                b_a = None
            if series.user_group != u_gp:
                u_gp = None
            if series.data_group != d_gp:
                d_gp = None

        ts = [series.t for series in self.series]
        ms = [series.mass for series in self.series]
        es = [series.errs for series in self.series]

        t, m = ts_combine(ts, ms)  # TODO: averaging modes
        _, e = ts_combine(ts, es, error=True)

        return MassChangeDataSeries(None, u_gp, d_gp, b_gp, b_id, b_a, t, None, m, e)

    def savemat(self, filename):
        data = {
            "t": [s.t for s in self],
            "dm": [s.mass for s in self],
            "e": [s.errs for s in self],
        }
        savemat(filename, data)

    def reduce(self, interval: float = 1.0, centre=None):
        out = MassChangeCollection()
        for s in self:
            out.add_series(s.reduce(interval=interval, centre=centre))
        return out

    def sum(self, error_method: ErrorMethod = ErrorMethod.sum) -> MassChangeDataSeries:
        if not self.series:
            return None
        elif len(self.series) == 1:
            return self.series[0]

        b_id = self.series[0].basin_id
        b_gp = self.series[0].basin_group
        b_a = self.series[0].basin_area

        u_gp = self.series[0].user_group
        d_gp = self.series[0].data_group

        for series in self:
            if series.basin_id != b_id:
                b_id = None
            if series.basin_group != b_gp:
                b_gp = None
            # if series.basin_area != b_a:
            #     b_a = None
            if series.user_group != u_gp:
                u_gp = None
            if series.data_group != d_gp:
                d_gp = None

        ts = [series.t for series in self.series]
        ms = [series.mass for series in self.series]
        es = [series.errs for series in self.series]

        t, m = sum_series(ts, ms)
        _, e = sum_series(ts, es)

        if error_method != ErrorMethod.sum:
            e = np.sqrt(e)

        return MassChangeDataSeries(None, u_gp, d_gp, b_gp, b_id, b_a, t, None, m, e)

    def differentiate(self) -> "model.collections.WorkingMassRateCollection":
        out = model.collections.WorkingMassRateCollection()
        for series in self:
            out.add_series(series.differentiate())
        return out

    def to_dmdt(
        self,
        truncate: bool = True,
        window: float = 1.0,
        method: LSQMethod = LSQMethod.normal,
        tapering: bool = False,
        monthly: bool = False,
    ) -> "model.collections.WorkingMassRateCollection":
        out = model.collections.WorkingMassRateCollection()

        #### IMBIE3 update - series is not put in collection if
        #### dm/dt is all NaN, which indicates failure of interpolation
        
        for series in self:
            test_series=model.series.WorkingMassRateDataSeries.from_dm(
                    series,
                    truncate=truncate,
                    window=window,
                    method=method,
                    tapering=tapering,
                    monthly=monthly,
                )
            if ~np.isnan(test_series.dmdt).all():
                out.add_series(test_series)
            else:
                print('Series ', series.user, series.data_group, series.basin_id, ' removed due to failure to convert dm timeseries to dm/dt timeseries')
        return out

    def filter(self, **kwargs) -> "MassChangeCollection":
        return super().filter(**kwargs)

    def align(self, reference: MassChangeDataSeries) -> "MassChangeCollection":
        return MassChangeCollection(*[series.align(reference) for series in self])

    def __add__(self, other: "MassChangeCollection") -> "MassChangeCollection":
        if isinstance(other, MassChangeDataSeries):
            return MassChangeCollection(*(self.series + [other]))
        elif isinstance(other, MassChangeCollection):
            return MassChangeCollection(*(self.series + other.series))
        else:
            raise ValueError()

    def __iadd__(self, other: "MassChangeCollection") -> "MassChangeCollection":
        self.series += other.series
        return self

    def smooth(self, window=None) -> "MassChangeCollection":
        if window is None:
            return self
        out = MassChangeCollection()
        for s in self:
            out.add_series(s.smooth(window=window))
        return out
