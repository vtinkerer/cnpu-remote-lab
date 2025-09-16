export type Measurements = {
  circuit_params: {
    vin: number;
    /**
     * Percentage
     */
    pwm_percentage: number;
    /**
     * microfarads
     */
    c_value: number;
    current_out: number;
    r_load: number;
    vout: number;
  };
  measurements: {
    voltage: number[];
    time: number[];
    pwm: number[];
    current: number[];
  };
};
