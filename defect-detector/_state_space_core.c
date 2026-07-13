/* Native core for the buck-converter state-space model.
 *
 * Mirrors StateSpaceBuckConverter in state_space_model.py exactly:
 * exact matrix-exponential discretization of the three affine topologies
 * (ON / OFF / DCM), periodic steady-state solve (closed-form in CCM,
 * frozen-clamp affine fixed point in DCM), then the recording loop.
 *
 * Compiled on demand by state_space_model.py:
 *   cc -O3 -shared -fPIC _state_space_core.c -o _state_space_core.so -lm
 * and called through ctypes (ss_simulate).
 */

#include <math.h>
#include <stdlib.h>
#include <string.h>

/* ---------- small dense linear algebra ---------- */

static void mv3(const double *A, const double *x, double *y)
{
    for (int i = 0; i < 3; i++)
        y[i] = A[i*3]*x[0] + A[i*3+1]*x[1] + A[i*3+2]*x[2];
}

/* x <- Ad x + bd */
static void step_affine(const double *Ad, const double *bd, double *x)
{
    double y[3];
    mv3(Ad, x, y);
    x[0] = y[0] + bd[0];
    x[1] = y[1] + bd[1];
    x[2] = y[2] + bd[2];
}

static void mm(int n, const double *A, const double *B, double *C)
{
    for (int i = 0; i < n; i++)
        for (int j = 0; j < n; j++) {
            double s = 0.0;
            for (int k = 0; k < n; k++)
                s += A[i*n+k] * B[k*n+j];
            C[i*n+j] = s;
        }
}

/* Solve A x = b (3x3), Gaussian elimination with partial pivoting.
 * Returns 0 on success, -1 if singular. */
static int solve3(const double *A_in, const double *b_in, double *x)
{
    double A[9], b[3];
    memcpy(A, A_in, sizeof A);
    memcpy(b, b_in, sizeof b);
    for (int col = 0; col < 3; col++) {
        int piv = col;
        for (int r = col + 1; r < 3; r++)
            if (fabs(A[r*3+col]) > fabs(A[piv*3+col]))
                piv = r;
        if (fabs(A[piv*3+col]) < 1e-300)
            return -1;
        if (piv != col) {
            for (int c = 0; c < 3; c++) {
                double t = A[col*3+c]; A[col*3+c] = A[piv*3+c]; A[piv*3+c] = t;
            }
            double t = b[col]; b[col] = b[piv]; b[piv] = t;
        }
        for (int r = col + 1; r < 3; r++) {
            double f = A[r*3+col] / A[col*3+col];
            for (int c = col; c < 3; c++)
                A[r*3+c] -= f * A[col*3+c];
            b[r] -= f * b[col];
        }
    }
    for (int r = 2; r >= 0; r--) {
        double s = b[r];
        for (int c = r + 1; c < 3; c++)
            s -= A[r*3+c] * x[c];
        x[r] = s / A[r*3+r];
    }
    return 0;
}

/* exp(A) for 4x4 A: scaling-and-squaring with a Taylor series */
static void expm4(const double *A, double *E)
{
    double norm = 0.0;
    for (int i = 0; i < 4; i++) {
        double s = 0.0;
        for (int j = 0; j < 4; j++)
            s += fabs(A[i*4+j]);
        if (s > norm) norm = s;
    }
    int s = 0;
    while (norm > 0.5) { norm *= 0.5; s++; }

    double As[16], term[16], tmp[16];
    for (int k = 0; k < 16; k++)
        As[k] = ldexp(A[k], -s);

    memset(E, 0, 16 * sizeof(double));
    memset(term, 0, sizeof term);
    for (int i = 0; i < 4; i++) { E[i*4+i] = 1.0; term[i*4+i] = 1.0; }

    for (int k = 1; k <= 30; k++) {
        mm(4, term, As, tmp);
        double mx = 0.0;
        for (int j = 0; j < 16; j++) {
            term[j] = tmp[j] / k;
            E[j] += term[j];
            double a = fabs(term[j]);
            if (a > mx) mx = a;
        }
        if (mx < 1e-19)
            break;
    }
    for (int i = 0; i < s; i++) {
        mm(4, E, E, tmp);
        memcpy(E, tmp, sizeof tmp);
    }
}

/* Exact discretization of dx/dt = A x + b over dt via the augmented expm */
static void discretize(const double *A, const double *b, double dt,
                       double *Ad, double *bd)
{
    double aug[16], E[16];
    memset(aug, 0, sizeof aug);
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++)
            aug[i*4+j] = A[i*3+j] * dt;
        aug[i*4+3] = b[i] * dt;
    }
    expm4(aug, E);
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++)
            Ad[i*3+j] = E[i*4+j];
        bd[i] = E[i*4+3];
    }
}

/* ---------- period stepping with DCM clamp ---------- */

/* Advance one PWM period. frozen_k >= 0 forces the clamp at that
 * off-substep (affine frozen map); otherwise the i_L <= 0 crossing is
 * detected. If rec is non-NULL, one 3-vector per substep is appended at
 * *pos. Returns the clamp substep index, or -1 if the clamp never engaged. */
static int step_period(double *x,
                       int n_on, const double *AdOn, const double *bdOn,
                       int n_off, const double *AdOff, const double *bdOff,
                       const double *AdDcm, const double *bdDcm,
                       int frozen_k, double *rec, long *pos)
{
    for (int i = 0; i < n_on; i++) {
        step_affine(AdOn, bdOn, x);
        if (rec) { memcpy(rec + (*pos) * 3, x, 3 * sizeof(double)); (*pos)++; }
    }
    int clamp = -1;
    for (int j = 0; j < n_off; j++) {
        if (clamp >= 0 && j > clamp) {
            step_affine(AdDcm, bdDcm, x);
        } else {
            step_affine(AdOff, bdOff, x);
            int hit = (frozen_k >= 0) ? (j == frozen_k) : (x[0] <= 0.0);
            if (hit) { x[0] = 0.0; clamp = j; }
        }
        if (rec) { memcpy(rec + (*pos) * 3, x, 3 * sizeof(double)); (*pos)++; }
    }
    return clamp;
}

/* ---------- entry point ---------- */

/* Simulate n_periods of periodic steady state.
 * A_* are row-major 3x3, b_* are 3-vectors (continuous-time dynamics).
 * out_states must hold (1 + n_periods*(n_on+n_off)) * 3 doubles.
 * Returns 0 on success, -1 on a singular solve. */
int ss_simulate(const double *A_on, const double *b_on,
                const double *A_off, const double *b_off,
                const double *A_dcm, const double *b_dcm,
                double ton, double toff,
                int n_on, int n_off, int n_periods,
                double vout_guess,
                double *out_states)
{
    double AdOn[9], bdOn[3], AdOff[9], bdOff[3], AdDcm[9], bdDcm[3];
    discretize(A_on, b_on, ton / n_on, AdOn, bdOn);
    discretize(A_off, b_off, toff / n_off, AdOff, bdOff);
    discretize(A_dcm, b_dcm, toff / n_off, AdDcm, bdDcm);

    double x0[3];
    int have_x0 = 0;

    /* CCM: closed-form fixed point of the two-interval period map */
    {
        double PhiOn[9], gamOn[3], PhiOff[9], gamOff[3];
        discretize(A_on, b_on, ton, PhiOn, gamOn);
        discretize(A_off, b_off, toff, PhiOff, gamOff);

        double P[9], M[9], rhs[3], t[3], xc[3];
        mm(3, PhiOff, PhiOn, P);
        mv3(PhiOff, gamOn, t);
        for (int i = 0; i < 3; i++) rhs[i] = t[i] + gamOff[i];
        for (int i = 0; i < 9; i++) M[i] = -P[i];
        for (int i = 0; i < 3; i++) M[i*3+i] += 1.0;

        if (solve3(M, rhs, xc) == 0 && xc[0] >= 0.0) {
            double xt[3];
            memcpy(xt, xc, sizeof xt);
            int clamp = step_period(xt, n_on, AdOn, bdOn, n_off, AdOff, bdOff,
                                    AdDcm, bdDcm, -1, 0, 0);
            if (clamp < 0) {
                memcpy(x0, xc, sizeof x0);
                have_x0 = 1;
            }
        }
    }

    /* DCM: fixed point of the frozen-clamp affine period map, iterating
     * on the clamp index until self-consistent */
    if (!have_x0) {
        double x[3] = { 0.0, 0.0, vout_guess };
        double xt[3];
        memcpy(xt, x, sizeof xt);
        int k = step_period(xt, n_on, AdOn, bdOn, n_off, AdOff, bdOff,
                            AdDcm, bdDcm, -1, 0, 0);
        for (int it = 0; it < 10; it++) {
            if (k < 0) k = n_off - 1;

            double q[3] = { 0.0, 0.0, 0.0 };
            step_period(q, n_on, AdOn, bdOn, n_off, AdOff, bdOff,
                        AdDcm, bdDcm, k, 0, 0);
            double P[9];
            for (int j = 0; j < 3; j++) {
                double e[3] = { 0.0, 0.0, 0.0 };
                e[j] = 1.0;
                step_period(e, n_on, AdOn, bdOn, n_off, AdOff, bdOff,
                            AdDcm, bdDcm, k, 0, 0);
                for (int i = 0; i < 3; i++)
                    P[i*3+j] = e[i] - q[i];
            }
            double M[9];
            for (int i = 0; i < 9; i++) M[i] = -P[i];
            for (int i = 0; i < 3; i++) M[i*3+i] += 1.0;
            if (solve3(M, q, x) != 0)
                return -1;
            if (x[0] < 0.0) x[0] = 0.0;

            double xn[3];
            memcpy(xn, x, sizeof xn);
            int kn = step_period(xn, n_on, AdOn, bdOn, n_off, AdOff, bdOff,
                                 AdDcm, bdDcm, -1, 0, 0);
            double d = 0.0;
            for (int i = 0; i < 3; i++) {
                double a = fabs(xn[i] - x[i]);
                if (a > d) d = a;
            }
            if (kn == k && d < 1e-7)
                break;
            k = kn;
        }
        memcpy(x0, x, sizeof x0);
    }

    /* Record the output window */
    memcpy(out_states, x0, 3 * sizeof(double));
    long pos = 1;
    double x[3];
    memcpy(x, x0, sizeof x);
    for (int p = 0; p < n_periods; p++)
        step_period(x, n_on, AdOn, bdOn, n_off, AdOff, bdOff,
                    AdDcm, bdDcm, -1, out_states, &pos);
    return 0;
}

/* Simulate and reduce to the four detector metrics in one call.
 *
 * out_stats[4] = { voltage_mean, voltage_ripple, current_mean,
 *                  current_ripple }, ripple defined as max - mean (same as
 * the analysis scripts). Only samples with t <= t_end (+1e-9 s tolerance)
 * enter the statistics, matching the Python packaging.
 *
 * out_states may be NULL (a scratch buffer is allocated internally) or a
 * caller buffer of (1 + n_periods*(n_on+n_off)) * 3 doubles to also get
 * the waveform. Returns 0 on success. */
int ss_simulate_stats(const double *A_on, const double *b_on,
                      const double *A_off, const double *b_off,
                      const double *A_dcm, const double *b_dcm,
                      double ton, double toff,
                      int n_on, int n_off, int n_periods,
                      double vout_guess,
                      double r_load, double t_end,
                      double *out_states, double *out_stats)
{
    long n_samples = 1 + (long)n_periods * (n_on + n_off);
    double *states = out_states;
    if (!states) {
        states = malloc(n_samples * 3 * sizeof(double));
        if (!states)
            return -1;
    }

    int status = ss_simulate(A_on, b_on, A_off, b_off, A_dcm, b_dcm,
                             ton, toff, n_on, n_off, n_periods,
                             vout_guess, states);
    if (status != 0) {
        if (!out_states) free(states);
        return status;
    }

    double T = ton + toff;
    double dt_on = ton / n_on, dt_off = toff / n_off;
    double v_sum = 0.0, i_sum = 0.0, v_max = -HUGE_VAL, i_max = -HUGE_VAL;
    long kept = 0;
    for (long k = 0; k < n_samples; k++) {
        double t;
        if (k == 0) {
            t = 0.0;
        } else {
            long j = k - 1;
            long per = j / (n_on + n_off), in = j % (n_on + n_off);
            t = per * T + (in < n_on ? (in + 1) * dt_on
                                     : ton + (in - n_on + 1) * dt_off);
        }
        if (t > t_end + 1e-9)
            continue;
        double i_l = states[k*3], i_c = states[k*3+1];
        double v = r_load * (i_l - i_c);
        v_sum += v;
        i_sum += i_l;
        if (v > v_max) v_max = v;
        if (i_l > i_max) i_max = i_l;
        kept++;
    }
    if (!out_states)
        free(states);
    if (kept == 0)
        return -1;

    double v_mean = v_sum / kept, i_mean = i_sum / kept;
    out_stats[0] = v_mean;
    out_stats[1] = v_max - v_mean;
    out_stats[2] = i_mean;
    out_stats[3] = i_max - i_mean;
    return 0;
}
