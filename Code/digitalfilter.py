"""
from https://www.samproell.io/posts/yarppg/yarppg-live-digital-filter/
"""

from collections import deque
import numpy as np
import scipy
from functools import reduce

class LiveFilter:
    """Base class for live filters.
    """
    def process(self, x):
        # do not process NaNs
        if np.isnan(x):
            return x

        return self._process(x)

    def __call__(self, x):
        return self.process(x)

    def _process(self, x):
        raise NotImplementedError("Derived class must implement _process")


class LiveLFilter(LiveFilter):
    """Live implementation of digital filter using difference equations.

    The following is almost equivalent to calling scipy.lfilter(b, a, xs):
    >>> lfilter = LiveLFilter(b, a)
    >>> [lfilter(x) for x in xs]
    """
    def __init__(self, b, a):
        """Initialize live filter based on difference equation.

        Args:
            b (array-like): numerator coefficients obtained from scipy
                filter design.
            a (array-like): denominator coefficients obtained from scipy
                filter design.
        """
        self.b = b
        self.a = a
        self._xs = deque([0] * len(b), maxlen=len(b))
        self._ys = deque([0] * (len(a) - 1), maxlen=len(a)-1)

    def _process(self, x):
        """Filter incoming data with standard difference equations.
        """
        self._xs.appendleft(x)
        y = np.dot(self.b, self._xs) - np.dot(self.a[1:], self._ys)
        y = y / self.a[0]
        self._ys.appendleft(y)

        return y


class LiveSosFilter(LiveFilter):
    """Live implementation of digital filter with second-order sections.

    The following is equivalent to calling scipy.sosfilt(sos, xs):
    >>> sosfilter = LiveSosFilter(sos)
    >>> [sosfilter(x) for x in xs]
    """
    def __init__(self, sos):
        """Initialize live second-order sections filter.

        Args:
            sos (array-like): second-order sections obtained from scipy
                filter design (with output="sos").
        """
        self.sos = sos

        self.n_sections = sos.shape[0]
        self.state = np.zeros((self.n_sections, 2))

    def _process(self, x):
        """Filter incoming data with cascaded second-order sections.
        """
        for s in range(self.n_sections):  # apply filter sections in sequence
            b0, b1, b2, a0, a1, a2 = self.sos[s, :]

            # compute difference equations of transposed direct form II
            y = b0*x + self.state[s, 0]
            self.state[s, 0] = b1*x - a1*y + self.state[s, 1]
            self.state[s, 1] = b2*x - a2*y
            x = y  # set biquad output as input of next filter section.

        return y

def get_Highpass_filter(order=4, cutoff=1, fs=30, output="ba"):
    coeffs = scipy.signal.iirfilter(order, Wn=cutoff, fs=fs, btype="highpass", ftype="butter", output=output)
    if output == "ba":
        return LiveLFilter(*coeffs)
    elif output == "sos":
        return LiveSosFilter(coeffs)
    
    raise NotImplementedError(f"Unknown output {output!r}")

def get_Biopotential_filter(order=4, cutoff=[0.5, 50], btype="bandpass", fs=30, output="ba", notch=True):
    """Create live filter with lfilter or sosfilt implmementation.
    """
    coeffs = scipy.signal.iirfilter(order, Wn=cutoff, fs=fs, btype=btype,
                                    ftype="butter", output=output)

    if output == "ba":
        if notch:
            notch_coeffs = scipy.signal.iirnotch(50, 30, fs)
            notch_filter = LiveLFilter(*notch_coeffs)
            biopotential_filter = LiveLFilter(*coeffs)
            filters = reduce(lambda a, b: lambda x: b(a(x)), [notch_filter, biopotential_filter])
            return filters
        else:
            return LiveLFilter(*coeffs)
    elif output == "sos":
        if notch:
            notch_coeffs = scipy.signal.iirnotch(50, 30, fs)
            notch_filter = LiveLFilter(*notch_coeffs)
            biopotential_filter = LiveSosFilter(coeffs)
            filters = reduce(lambda a, b: lambda x: b(a(x)), [notch_filter, biopotential_filter])
            return filters
        else:
            return LiveSosFilter(coeffs)

    raise NotImplementedError(f"Unknown output {output!r}")


# my old code
# filters = []

# # Notch filter parameters
# Fs = 320  # Sampling frequency in Hz
# f0 = 50  # Notch filter frequency in Hz
# Q = 30.0  # Quality factor
# b, a = iirnotch(f0, Q, Fs)
# notch_filter = LiveFilter(b, a)
# filters.append(notch_filter)

# # Lowpass filter parameters
# f_low_pass = 20  # Cutoff frequency of lowpass filter in Hz
# order = 16  # Filter order
# b_lowpass, a_lowpass = iirfilter(order, f_low_pass, fs=Fs, btype='lowpass')
# lowpass_filter = LiveFilter(b_lowpass, a_lowpass)
# filters.append(lowpass_filter)

# # Highpass filter parameters
# f_high_pass = 1  # Cutoff frequency of highpass filter in Hz
# order = 4  # Filter order
# b_highpass, a_highpass = iirfilter(order, f_high_pass, fs=Fs, btype='highpass')
# highpass_filter = LiveFilter(b_highpass, a_highpass)
# filters.append(highpass_filter)

# apply_filters = reduce(lambda a, b: lambda x: b(a(x)), filters)


# # Bandstop filter parameters
# Fs = 222  # Sampling frequency in Hz
# Fs = 320  # Sampling frequency in Hz
# low_cutoff = 45  # Lower cutoff frequency in Hz
# high_cutoff = 55  # Higher cutoff frequency in Hz
# order_bandstop = 16  # Bandstop filter order

# coeffs = iirfilter(order_bandstop, [low_cutoff, high_cutoff], btype='bandstop', fs=Fs, ftype='butter', output='sos')
# bandstop_filter = LiveSosFilter(coeffs)
# filters.append(bandstop_filter)

# # Lowpass filter parameters
# f_low_pass = 20  # Cutoff frequency of lowpass filter in Hz
# order_lowpass = 16  # Lowpass filter order
# coeffs = iirfilter(order_lowpass, f_low_pass, btype='lowpass', fs=Fs, ftype='butter', output='sos')
# lowpass_filter = LiveSosFilter(coeffs)
# filters.append(lowpass_filter)
