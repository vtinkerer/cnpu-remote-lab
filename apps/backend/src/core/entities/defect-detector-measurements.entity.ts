export type DefectDetectorAnalysisResult = {
  sim_vout_avg: number;
  sim_vout_ripple: number;
  sim_il_avg: boolean;
  sim_il_ripple: number;
  measured_vout_avg: number;
  measured_vout_ripple: number;
  measured_il_avg: number;
  measured_il_ripple: number;
  percentage_difference_avg_vout: number;
  percentage_difference_ripple_vout: number;
  percentage_difference_avg_il: number;
  percentage_difference_ripple_il: number;
};
