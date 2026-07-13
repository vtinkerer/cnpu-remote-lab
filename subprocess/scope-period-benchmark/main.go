// scope-period-benchmark measures how long it takes to capture one full
// switching period (~3.33 us @ 300 kHz) of the DC-DC converter voltage and
// current signals from an Analog Discovery 2.
//
// It mirrors the production capture setup in subprocess/scope/scope-subprocess.py:
//   - scope channel 1 (index 0): converter output voltage
//   - scope channel 2 (index 1): current shunt, converted as (V - 0.65) * 10 [A]
//   - sampling frequency 100 MHz, trigger from PWM on DIO 0 (rising edge)
//
// Unlike the Python subprocess (which runs two scope.record() calls, i.e. two
// full acquisitions), both channels here are read from a SINGLE acquisition —
// the hardware always digitizes both channels simultaneously.
//
// For each iteration:
//  1. capture timestamp before
//  2. arm the scope, wait for the acquisition to complete, read both channels
//  3. capture timestamp after
//  4. report the elapsed time
//
// Usage:
//
//	go run . [-n 100] [-samples 334] [-freq 100e6] [-range 5] [-trigger digital|none] [-dump]
package main

import (
	"flag"
	"fmt"
	"log"
	"math"
	"os"
	"sort"
	"time"

	"github.com/ebitengine/purego"
)

// sigStats describes one captured period of a signal: DC mean, peak-to-peak
// ripple and RMS (standard deviation) ripple around the mean.
type sigStats struct {
	mean      float64
	ripplePP  float64
	rippleRMS float64
}

func analyze(samples []float64) sigStats {
	min, max, sum := samples[0], samples[0], 0.0
	for _, v := range samples {
		if v < min {
			min = v
		}
		if v > max {
			max = v
		}
		sum += v
	}
	mean := sum / float64(len(samples))
	var acc float64
	for _, v := range samples {
		d := v - mean
		acc += d * d
	}
	return sigStats{
		mean:      mean,
		ripplePP:  max - min,
		rippleRMS: math.Sqrt(acc / float64(len(samples))),
	}
}

func (s *sigStats) add(o sigStats) {
	s.mean += o.mean
	s.ripplePP += o.ripplePP
	s.rippleRMS += o.rippleRMS
}

func (s *sigStats) div(n float64) {
	s.mean /= n
	s.ripplePP /= n
	s.rippleRMS /= n
}

// DWF constants (from dwfconstants.py)
const (
	trigsrcNone              = 0
	trigsrcDetectorDigitalIn = 3
	stateDone                = 2 // DwfStateDone
	filterDecimate           = 0
)

var (
	FDwfDeviceOpen                    func(index int32, handle *int32) int32
	FDwfDeviceClose                   func(handle int32) int32
	FDwfDeviceAutoConfigureSet        func(handle int32, autoConfigure int32) int32
	FDwfGetLastErrorMsg               func(msg *byte) int32
	FDwfAnalogInChannelEnableSet      func(handle int32, idxChannel int32, enable int32) int32
	FDwfAnalogInChannelOffsetSet      func(handle int32, idxChannel int32, offset float64) int32
	FDwfAnalogInChannelRangeSet       func(handle int32, idxChannel int32, volts float64) int32
	FDwfAnalogInChannelFilterSet      func(handle int32, idxChannel int32, filter int32) int32
	FDwfAnalogInBufferSizeSet         func(handle int32, size int32) int32
	FDwfAnalogInBufferSizeGet         func(handle int32, size *int32) int32
	FDwfAnalogInFrequencySet          func(handle int32, hz float64) int32
	FDwfAnalogInFrequencyGet          func(handle int32, hz *float64) int32
	FDwfAnalogInConfigure             func(handle int32, reconfigure int32, start int32) int32
	FDwfAnalogInStatus                func(handle int32, readData int32, state *byte) int32
	FDwfAnalogInStatusData            func(handle int32, idxChannel int32, data *float64, count int32) int32
	FDwfAnalogInTriggerSourceSet      func(handle int32, src int32) int32
	FDwfAnalogInTriggerAutoTimeoutSet func(handle int32, secs float64) int32
	FDwfDigitalInTriggerSourceSet     func(handle int32, src int32) int32
	FDwfDigitalInTriggerSet           func(handle int32, levelLow uint32, levelHigh uint32, edgeRise uint32, edgeFall uint32) int32
	FDwfDigitalInTriggerResetSet      func(handle int32, levelLow uint32, levelHigh uint32, edgeRise uint32, edgeFall uint32) int32
)

func initDwf() {
	dwf, err := purego.Dlopen("libdwf.so", purego.RTLD_NOW|purego.RTLD_GLOBAL)
	if err != nil {
		log.Fatalf("error loading libdwf.so: %v", err)
	}
	purego.RegisterLibFunc(&FDwfDeviceOpen, dwf, "FDwfDeviceOpen")
	purego.RegisterLibFunc(&FDwfDeviceClose, dwf, "FDwfDeviceClose")
	purego.RegisterLibFunc(&FDwfDeviceAutoConfigureSet, dwf, "FDwfDeviceAutoConfigureSet")
	purego.RegisterLibFunc(&FDwfGetLastErrorMsg, dwf, "FDwfGetLastErrorMsg")
	purego.RegisterLibFunc(&FDwfAnalogInChannelEnableSet, dwf, "FDwfAnalogInChannelEnableSet")
	purego.RegisterLibFunc(&FDwfAnalogInChannelOffsetSet, dwf, "FDwfAnalogInChannelOffsetSet")
	purego.RegisterLibFunc(&FDwfAnalogInChannelRangeSet, dwf, "FDwfAnalogInChannelRangeSet")
	purego.RegisterLibFunc(&FDwfAnalogInChannelFilterSet, dwf, "FDwfAnalogInChannelFilterSet")
	purego.RegisterLibFunc(&FDwfAnalogInBufferSizeSet, dwf, "FDwfAnalogInBufferSizeSet")
	purego.RegisterLibFunc(&FDwfAnalogInBufferSizeGet, dwf, "FDwfAnalogInBufferSizeGet")
	purego.RegisterLibFunc(&FDwfAnalogInFrequencySet, dwf, "FDwfAnalogInFrequencySet")
	purego.RegisterLibFunc(&FDwfAnalogInFrequencyGet, dwf, "FDwfAnalogInFrequencyGet")
	purego.RegisterLibFunc(&FDwfAnalogInConfigure, dwf, "FDwfAnalogInConfigure")
	purego.RegisterLibFunc(&FDwfAnalogInStatus, dwf, "FDwfAnalogInStatus")
	purego.RegisterLibFunc(&FDwfAnalogInStatusData, dwf, "FDwfAnalogInStatusData")
	purego.RegisterLibFunc(&FDwfAnalogInTriggerSourceSet, dwf, "FDwfAnalogInTriggerSourceSet")
	purego.RegisterLibFunc(&FDwfAnalogInTriggerAutoTimeoutSet, dwf, "FDwfAnalogInTriggerAutoTimeoutSet")
	purego.RegisterLibFunc(&FDwfDigitalInTriggerSourceSet, dwf, "FDwfDigitalInTriggerSourceSet")
	purego.RegisterLibFunc(&FDwfDigitalInTriggerSet, dwf, "FDwfDigitalInTriggerSet")
	purego.RegisterLibFunc(&FDwfDigitalInTriggerResetSet, dwf, "FDwfDigitalInTriggerResetSet")
}

func lastError() string {
	msg := make([]byte, 512)
	FDwfGetLastErrorMsg(&msg[0])
	n := 0
	for n < len(msg) && msg[n] != 0 {
		n++
	}
	return string(msg[:n])
}

func check(ret int32, what string) {
	if ret == 0 {
		log.Fatalf("%s failed: %s", what, lastError())
	}
}

func main() {
	iterations := flag.Int("n", 100, "number of timed captures")
	samples := flag.Int("samples", 334, "samples per capture (334 @ 100 MHz = one 3.33 us period)")
	freq := flag.Float64("freq", 100e6, "sampling frequency, Hz")
	vrange := flag.Float64("range", 5, "scope amplitude range, V (production uses 20 for Vin > 2.5)")
	triggerMode := flag.String("trigger", "digital", "trigger mode: digital (PWM on DIO 0, as in production) or none (free-run)")
	dump := flag.Bool("dump", false, "print voltage/current samples of the last capture")
	flag.Parse()

	initDwf()

	var handle int32
	if FDwfDeviceOpen(-1, &handle); handle == 0 {
		log.Fatalf("failed to open Analog Discovery device: %s", lastError())
	}
	defer FDwfDeviceClose(handle)

	// Apply instrument settings only on explicit Configure calls instead of
	// after every Set call — avoids a USB round trip per setting.
	check(FDwfDeviceAutoConfigureSet(handle, 0), "FDwfDeviceAutoConfigureSet")

	// Scope setup, mirroring WF_SDK scope.open() (channel index -1 = all channels)
	check(FDwfAnalogInChannelEnableSet(handle, -1, 1), "FDwfAnalogInChannelEnableSet")
	check(FDwfAnalogInChannelOffsetSet(handle, -1, 0), "FDwfAnalogInChannelOffsetSet")
	check(FDwfAnalogInChannelRangeSet(handle, -1, *vrange), "FDwfAnalogInChannelRangeSet")
	check(FDwfAnalogInBufferSizeSet(handle, int32(*samples)), "FDwfAnalogInBufferSizeSet")
	check(FDwfAnalogInFrequencySet(handle, *freq), "FDwfAnalogInFrequencySet")
	check(FDwfAnalogInChannelFilterSet(handle, -1, filterDecimate), "FDwfAnalogInChannelFilterSet")

	switch *triggerMode {
	case "digital":
		// Same as production: scope triggered by the digital-in detector on
		// DIO 0 rising edge (the PWM line), 0.2 s auto-trigger fallback.
		check(FDwfDigitalInTriggerSourceSet(handle, trigsrcDetectorDigitalIn), "FDwfDigitalInTriggerSourceSet")
		mask := uint32(1) << 0
		check(FDwfDigitalInTriggerSet(handle, 0, mask, 0, 0), "FDwfDigitalInTriggerSet")
		check(FDwfDigitalInTriggerResetSet(handle, 0, 0, mask, 0), "FDwfDigitalInTriggerResetSet")
		check(FDwfAnalogInTriggerSourceSet(handle, trigsrcDetectorDigitalIn), "FDwfAnalogInTriggerSourceSet")
		check(FDwfAnalogInTriggerAutoTimeoutSet(handle, 0.2), "FDwfAnalogInTriggerAutoTimeoutSet")
	case "none":
		check(FDwfAnalogInTriggerSourceSet(handle, trigsrcNone), "FDwfAnalogInTriggerSourceSet")
	default:
		log.Fatalf("unknown trigger mode %q", *triggerMode)
	}

	// Commit configuration to the device without starting an acquisition.
	check(FDwfAnalogInConfigure(handle, 1, 0), "FDwfAnalogInConfigure(commit)")

	// The device may round buffer size / frequency; report actual values.
	var actualSamples int32
	var actualFreq float64
	FDwfAnalogInBufferSizeGet(handle, &actualSamples)
	FDwfAnalogInFrequencyGet(handle, &actualFreq)
	acqWindowUs := float64(actualSamples) / actualFreq * 1e6
	fmt.Printf("scope: %d samples @ %.0f MHz -> capture window %.2f us (signal period 3.33 us), range ±%.0f V, trigger=%s\n",
		actualSamples, actualFreq/1e6, acqWindowUs, *vrange, *triggerMode)

	voltage := make([]float64, actualSamples)
	current := make([]float64, actualSamples)

	captureOnce := func() time.Duration {
		t0 := time.Now() // 1. timestamp before

		// 2. arm scope and wait for one full acquisition (both channels at once)
		check(FDwfAnalogInConfigure(handle, 0, 1), "FDwfAnalogInConfigure(start)")
		var state byte
		for {
			check(FDwfAnalogInStatus(handle, 1, &state), "FDwfAnalogInStatus")
			if state == stateDone {
				break
			}
		}
		check(FDwfAnalogInStatusData(handle, 0, &voltage[0], actualSamples), "FDwfAnalogInStatusData(voltage)")
		check(FDwfAnalogInStatusData(handle, 1, &current[0], actualSamples), "FDwfAnalogInStatusData(current)")
		for i := range current {
			current[i] = (current[i] - 0.65) * 10 // shunt output -> Amperes
		}

		t1 := time.Now() // 3. timestamp after
		return t1.Sub(t0)
	}

	// Warm-up capture: the first arm after reconfiguration is slower.
	warmup := captureOnce()
	fmt.Printf("warm-up capture: %v\n\n", warmup)

	durations := make([]time.Duration, *iterations)
	var vAvg, iAvg sigStats
	for i := range durations {
		durations[i] = captureOnce()
		// signal stats are computed outside the timed section so they don't
		// affect the capture-time measurement
		vAvg.add(analyze(voltage))
		iAvg.add(analyze(current))
	}
	vAvg.div(float64(*iterations))
	iAvg.div(float64(*iterations))

	// 4. calculate the time
	sorted := append([]time.Duration(nil), durations...)
	sort.Slice(sorted, func(i, j int) bool { return sorted[i] < sorted[j] })
	var total time.Duration
	for _, d := range sorted {
		total += d
	}
	mean := total / time.Duration(len(sorted))
	median := sorted[len(sorted)/2]
	p95 := sorted[len(sorted)*95/100]

	fmt.Printf("timed captures: %d\n", *iterations)
	fmt.Printf("  min:    %v\n", sorted[0])
	fmt.Printf("  median: %v\n", median)
	fmt.Printf("  mean:   %v\n", mean)
	fmt.Printf("  p95:    %v\n", p95)
	fmt.Printf("  max:    %v\n", sorted[len(sorted)-1])
	fmt.Printf("acquisition window itself: %.2f us -> overhead (median): %.1fx\n",
		acqWindowUs, float64(median.Microseconds())/acqWindowUs)

	fmt.Printf("\nsignal stats (averaged over %d captures of one period):\n", *iterations)
	fmt.Printf("  voltage: mean %.4f V, ripple %.4f Vpp (%.4f V rms)\n",
		vAvg.mean, vAvg.ripplePP, vAvg.rippleRMS)
	fmt.Printf("  current: mean %.4f A, ripple %.4f App (%.4f A rms)\n",
		iAvg.mean, iAvg.ripplePP, iAvg.rippleRMS)

	if *dump {
		fmt.Fprintln(os.Stderr, "idx\ttime_us\tvoltage_V\tcurrent_A")
		for i := int32(0); i < actualSamples; i++ {
			fmt.Fprintf(os.Stderr, "%d\t%.3f\t%.4f\t%.4f\n", i, float64(i)/actualFreq*1e6, voltage[i], current[i])
		}
	}
}
