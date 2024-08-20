import matplotlib.pyplot as plt
import numpy as np
from Waveforms.Waveform import Waveform

class PlottingTools:

    def plotCombined(raw: Waveform, biquad: Waveform, ax: plt.Axes=None, title = None):
        if ax is None:
            fig, ax = plt.subplots(figsize=(25, 15))

        ax.plot(raw.waveform[280:792], label='raw')
        ax.plot(biquad.waveform[401:913], label='biquad')

        # ax.plot(raw.timelist[280:792]*10**9, raw.waveform[280:792], label='raw')
        # ax.plot(biquad.timelist[401:913]*10**9, biquad.waveform[401:913], label='biquad')


        if title is not None:
            ax.set_title(title)
        ax.set_xlabel('time (ns)')
        ax.set_ylabel('ADC Counts', labelpad=-3.5)
        ax.legend()

    def plotDiff(raw: Waveform, biquad: Waveform, ax: plt.Axes=None, title = None):
        if ax is None:
            fig, ax = plt.subplots(figsize=(25, 15))

        ax.scatter(raw.timelist[280:792]*10**9,raw.waveform[280:792]-biquad.waveform[401:913], label='diff')

        # ax.plot(raw.timelist[280:792]*10**9, raw.waveform[280:792], label='raw')
        # ax.plot(biquad.timelist[401:913]*10**9, biquad.waveform[401:913], label='biquad')


        if title is not None:
            ax.set_title(title)
        ax.set_xlabel('time (ns)')
        ax.set_ylabel('ADC Counts', labelpad=-3.5)
        ax.legend()

    def plotBiquadShort(data: Waveform, ax: plt.Axes=None, title = None):
        if ax is None:
            fig, ax = plt.subplots(figsize=(16, 10))
        
        ax.plot(data.timelist[401:897]*10**9, data.waveform[401:897])
        # ax.plot(data.timelist*10**9, data.waveform)

        if title is not None:
            ax.set_title(title)
        ax.set_xlabel('time (ns)')
        ax.set_ylabel('ADC Counts', labelpad=-3.5)

        data.setOffset()
        data.setPeaktoPeak()
        data.setWaveFFT()
        
        ax.axhline(y=data.offset, color='black', linewidth=0.4, label='Offset')
        ax.axhline(y=data.peakToPeak+data.offset, color='black', linestyle='--', linewidth=0.3, label='RMS Line')
        ax.axhline(y=-data.peakToPeak+data.offset, color='black', linestyle='--', linewidth=0.3, label='RMS Line')

        stats_text = f"Amplitude : {data.peakToPeak:.2f} ADC\nFrequency : {data.frequencyFFT*10**(-6):.2f} MHz\nOffset : {data.offset:.2f} ADC"
        
        ax.text(0.97, 0.97, stats_text, verticalalignment='top', horizontalalignment='right',
            transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.5))
        

    def plotBiquad(data: Waveform, ax: plt.Axes=None, title = None):
        if ax is None:
            fig, ax = plt.subplots(figsize=(16, 10))
        
        ax.plot(data.timelist[401:913]*10**9, data.waveform[401:913])
        # ax.plot(data.timelist*10**9, data.waveform)

        if title is not None:
            ax.set_title(title)
        ax.set_xlabel('time (ns)')
        ax.set_ylabel('ADC Counts', labelpad=-3.5)

        data.setOffset()
        data.setPeaktoPeak()
        data.setWaveFFT()
        
        ax.axhline(y=data.offset, color='black', linewidth=0.4, label='Offset')
        ax.axhline(y=data.peakToPeak+data.offset, color='black', linestyle='--', linewidth=0.3, label='RMS Line')
        ax.axhline(y=-data.peakToPeak+data.offset, color='black', linestyle='--', linewidth=0.3, label='RMS Line')

        stats_text = f"Amplitude : {data.peakToPeak:.2f} ADC\nFrequency : {data.frequencyFFT*10**(-6):.2f} MHz\nOffset : {data.offset:.2f} ADC"
        
        ax.text(0.97, 0.97, stats_text, verticalalignment='top', horizontalalignment='right',
            transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.5))

    def plotGated(data: Waveform, ax: plt.Axes=None, title = None):
        
        if ax is None:
            fig, ax = plt.subplots(figsize=(16, 10))
        
        ax.plot(data.timelist[280:792]*10**9, data.waveform[280:792])

        if title is not None:
            ax.set_title(title)
        ax.set_xlabel('time (ns)')
        ax.set_ylabel('ADC Counts', labelpad=-3.5)

        data.setOffset()
        data.setRMS()
        data.setPeaktoPeak()
        data.setWaveFFT()
        
        ax.axhline(y=data.offset, color='black', linewidth=0.4, label='Offset')
        ax.axhline(y=data.RMS+data.offset, color='black', linestyle='--', linewidth=0.3, label='RMS Line')
        ax.axhline(y=-data.RMS+data.offset, color='black', linestyle='--', linewidth=0.3, label='RMS Line')

        stats_text = f"RMS : {data.RMS:.2f} ADC\nFrequency : {data.frequencyFFT*10**(-6):.2f} MHz"
        
        ax.text(0.97, 0.97, stats_text, verticalalignment='top', horizontalalignment='right',
            transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.5))


    def plotWaveForm(data: Waveform, ax: plt.Axes=None, title = None):
        
        if ax is None:
            fig, ax = plt.subplots(figsize=(16, 10))
        
        ax.plot(data.timelist*10**9, data.waveform)
        
        if title is not None:
            ax.set_title(title)
        ax.set_xlabel('time (ns)')
        ax.set_ylabel('ADC Counts', labelpad=-3.5)
        
        data.setRMS()
        data.setOffset()
        data.setWaveFFT()
        
        ax.axhline(y=data.offset, color='black', linewidth=0.4, label='Offset')
            
            
        stats_text = f"RMS : {data.RMS:.2f} ADC\nFrequency : {data.frequencyFFT*10**(-6):.2f} MHz\nOffset : {data.offset:.2f} ADC"
        
        ax.text(0.97, 0.97, stats_text, verticalalignment='top', horizontalalignment='right',
            transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.5))


    def plotAGC(data: Waveform, ax: plt.Axes=None, title = None):
        if ax is None:
            fig, ax = plt.subplots(figsize=(16, 10))
        
        ax.plot(data.timelist*10**9, data.waveform)

        if title is not None:
            ax.set_title(title)
        ax.set_xlabel('time (ns)')
        ax.set_ylabel('ADC Counts', labelpad=-3.5)

        data.setPeaktoPeak()
        data.setOffset()
        
        ax.axhline(y=data.offset, color='black', linewidth=0.4, label='Offset')
        ax.axhline(y=data.peakToPeak+data.offset, color='blue', linestyle='--', linewidth=0.7, alpha = 0.8, label='Peak to Peak Amplitude')
        ax.axhline(y=-data.peakToPeak+data.offset, color='blue', linestyle='--', linewidth=0.7, alpha = 0.8)

    def plotData(data: Waveform, ax: plt.Axes=None, title = None):
        
        # if data.peakToPeak is None:
        data.doAmps()
        
        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 8))

        if title is not None:
            ax.set_title(title)
        ax.set_xlabel('time (ns)')
        ax.set_ylabel('ADC Counts', labelpad=-3.5)
        
        ax.plot(data.timelist, data.waveform)
        stats_text = f"Peak-to-Peak {data.peakToPeak:.2f} ADC Counts\nFFT          {data.amplitudeFFT:.2f} ADC Counts\nRMS         {data.RMS:.2f} ADC Counts\nFrequency: {data.frequencyFFT/10**6:.2f} MHz"
        
        # ax.axhline(y=data.peakToPeak+data.offset, color='blue', linestyle='--', linewidth=0.7, alpha = 0.8, label='Peak to Peak Amplitude')
        # ax.axhline(y=-data.peakToPeak+data.offset, color='blue', linestyle='--', linewidth=0.7, alpha = 0.8)
        
        # ax.axhline(y=data.amplitudeFFT+data.offset, color='orange', linestyle='--', linewidth=0.7, alpha = 0.8, label='FFT Amplitude')
        # ax.axhline(y=-data.amplitudeFFT+data.offset, color='orange', linestyle='--', linewidth=0.7, alpha = 0.8)
        
        # ax.axhline(y=data.RMS+data.offset, color='red', linestyle='--', linewidth=0.7, alpha = 0.8, label='RMS Amplitude')
        # ax.axhline(y=-data.RMS+data.offset, color='red', linestyle='--', linewidth=0.7, alpha = 0.8)        
        
        ax.axhline(y=0, color='black', linewidth=0.8)
        
        ax.text(1.05, 1.05, stats_text, verticalalignment='top', horizontalalignment='right',
                 transform=plt.gca().transAxes, bbox=dict(facecolor='white', alpha=0.7))
        
    def plotFFT(data: Waveform, ax: plt.Axes=None, title=None):
        if ax is None:
            fig, ax = plt.subplots(figsize=(16, 10))
        
        try:
            data.doFFTs()
            ax.plot(data.xf*10**(-6), 20 * np.log10(data.mag_spectrum), label='scipy FFT')
        except:
            print("It's just not possible")

        if title is not None:
            ax.set_title(title)
        ax.set_xlabel("Frequency (MHz)")
        ax.set_ylabel("Magnitude (arb.)")
        
        
        stats_text = f"Frequency : {data.frequencyFFT*10**(-6):.2f} MHz\nAmplitude : {data.amplitudeFFT:.2f} ADC"
        
        ax.text(0.97, 0.97, stats_text, verticalalignment='top', horizontalalignment='right',
            transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.5))