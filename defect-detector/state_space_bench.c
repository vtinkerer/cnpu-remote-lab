/* Standalone benchmark for the state-space buck-converter core.
 * No Python required — builds the circuit matrices in C and times
 * ss_simulate() with clock_gettime(CLOCK_MONOTONIC).
 *
 * Build (on any Linux, incl. Raspberry Pi):
 *   gcc -O3 -o state_space_bench state_space_bench.c _state_space_core.c -lm
 * Run:
 *   ./state_space_bench [repeats]     (default 2000)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

int ss_simulate_stats(const double *A_on, const double *b_on,
                      const double *A_off, const double *b_off,
                      const double *A_dcm, const double *b_dcm,
                      double ton, double toff,
                      int n_on, int n_off, int n_periods,
                      double vout_guess,
                      double r_load, double t_end,
                      double *out_states, double *out_stats);

/* ---- fixed model constants (mirror state_space_model.py) ---- */
static const double FREQ = 312500.0;
static const double L_VALUE = 10e-6;
static const double L_RESISTANCE = 19.5e-3;
static const double VT_25C = 1.380649e-23 * 298.15 / 1.602176634e-19;

/* optimized parameters (defect-detector/optimized_parameters.json) */
static const double GATE_RISE_TIME = 1.0072085534880547e-10;
static const double GATE_FALL_TIME = 8.265072857706626e-08;
static const double SWITCH_RON = 3.3157359136705763e-12;
static const double DIODE_RS = 1e-06;
static const double DIODE_IS = 2.423465389750961e-15;
static const double CAP_ESR = 0.08779711061951505;
static const double CAP_INDUCTANCE = 3.215742370055204e-10;

/* measurement grid: 600 points, 0 .. 5.99 us, dt = 0.01 us */
static const double T_END = 5.99e-6;
static const double DT_TARGET = 0.01e-6 * 0.5;

typedef struct {
    const char *name;
    double vin, c_uF, pwm_pct, r_load;
} Case;

static double now_s(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

static int cmp_double(const void *a, const void *b)
{
    double d = *(const double *)a - *(const double *)b;
    return (d > 0) - (d < 0);
}

int main(int argc, char **argv)
{
    int repeats = (argc > 1) ? atoi(argv[1]) : 2000;

    Case cases[] = {
        { "Nominal (Vin=12, D=50%, R=4.1)", 12, 44, 50, 4.1 },
        { "Low Vin (Vin=6)",                 6, 44, 50, 4.1 },
        { "High duty (D=60%)",              12, 44, 60, 4.1 },
        { "Light load (R=15)",              12, 44, 50, 15  },
        { "DCM (D=5%)",                     12, 44,  5, 4.1 },
    };
    int n_cases = sizeof cases / sizeof cases[0];

    double *times = malloc(repeats * sizeof(double));

    printf("state-space core benchmark, %d repeats per case\n\n", repeats);
    printf("%-34s %10s %10s %10s | %9s %9s %9s %9s\n",
           "case", "min us", "med us", "mean us",
           "V_mean", "V_rip", "I_mean", "I_rip");

    for (int c = 0; c < n_cases; c++) {
        Case *p = &cases[c];
        double T = 1.0 / FREQ;
        double C = p->c_uF * 1e-6;
        double duty = p->pwm_pct / 100.0;

        /* effective on-time incl. gate ramp threshold crossings */
        double ton = duty * T + 0.9 * (GATE_RISE_TIME + GATE_FALL_TIME);
        if (ton < 0) ton = 0;
        if (ton > T) ton = T;
        double toff = T - ton;

        int n_on = (int)round(ton / DT_TARGET);  if (n_on < 1) n_on = 1;
        int n_off = (int)round(toff / DT_TARGET); if (n_off < 1) n_off = 1;
        int n_periods = (int)ceil(T_END / T) + 1;

        /* analytic operating point -> diode forward drop */
        double vout_ideal = p->vin * duty;
        double il_avg = vout_ideal / p->r_load;
        double vout = vout_ideal - il_avg * L_RESISTANCE;
        il_avg = vout / p->r_load;
        vout = vout_ideal - il_avg * L_RESISTANCE;
        double i_op = il_avg > 1e-6 ? il_avg : 1e-6;
        double v_f = VT_25C * log(i_op / DIODE_IS + 1.0);

        /* continuous-time A/b for the three topologies, x=[i_L,i_C,v_C] */
        double Lc = CAP_INDUCTANCE, Rl = L_RESISTANCE, Resr = CAP_ESR;
        double Rload = p->r_load;
        double row_ic[3] = { Rload / Lc, -(Rload + Resr) / Lc, -1.0 / Lc };
        double row_vc[3] = { 0.0, 1.0 / C, 0.0 };

        double A_on[9]  = { -(SWITCH_RON + Rload + Rl) / L_VALUE, Rload / L_VALUE, 0.0,
                            row_ic[0], row_ic[1], row_ic[2],
                            row_vc[0], row_vc[1], row_vc[2] };
        double b_on[3]  = { p->vin / L_VALUE, 0.0, 0.0 };
        double A_off[9] = { -(DIODE_RS + Rload + Rl) / L_VALUE, Rload / L_VALUE, 0.0,
                            row_ic[0], row_ic[1], row_ic[2],
                            row_vc[0], row_vc[1], row_vc[2] };
        double b_off[3] = { -v_f / L_VALUE, 0.0, 0.0 };
        double A_dcm[9] = { 0.0, 0.0, 0.0,
                            row_ic[0], row_ic[1], row_ic[2],
                            row_vc[0], row_vc[1], row_vc[2] };
        double b_dcm[3] = { 0.0, 0.0, 0.0 };

        /* Timed region = full simulation + metric reduction, exactly what
         * a deployed detector would run per reference simulation. The
         * scratch waveform buffer is provided so allocation cost is not
         * measured. */
        long n_samples = 1 + (long)n_periods * (n_on + n_off);
        double *states = malloc(n_samples * 3 * sizeof(double));
        double stats[4];

        for (int r = 0; r < repeats; r++) {
            double t0 = now_s();
            int status = ss_simulate_stats(A_on, b_on, A_off, b_off,
                                           A_dcm, b_dcm,
                                           ton, toff, n_on, n_off, n_periods,
                                           vout, Rload, T_END, states, stats);
            times[r] = (now_s() - t0) * 1e6;
            if (status != 0) {
                fprintf(stderr, "ss_simulate_stats failed on %s\n", p->name);
                return 1;
            }
        }

        qsort(times, repeats, sizeof(double), cmp_double);
        double mean = 0;
        for (int r = 0; r < repeats; r++) mean += times[r];
        mean /= repeats;

        printf("%-34s %10.1f %10.1f %10.1f | %9.4f %9.4f %9.4f %9.4f\n",
               p->name, times[0], times[repeats/2], mean,
               stats[0], stats[1], stats[2], stats[3]);
        free(states);
    }
    free(times);
    return 0;
}
