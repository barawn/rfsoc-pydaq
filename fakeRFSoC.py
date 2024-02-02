import numpy as np

class FakeOverlay:
    def __init__(self):
        return


class FakeRFSoC(FakeOverlay):
    def __init__(self):
        self.sampleRate = 3.E9
        self.frequency = 24.E6
        self.amplitude = 100
        return

    def internal_capture(self, buf, numChan):
        period = self.sampleRate/self.frequency
        numSamples = len(buf[0])
        for i in range(numChan):
            phase = np.random.ranf()*2*np.pi
            # We want sin(2pi t/period)
            for j in range(numSamples):
                val = np.int16(self.amplitude*np.sin(2*np.pi*j/period + phase))
                buf[i][j] = val

