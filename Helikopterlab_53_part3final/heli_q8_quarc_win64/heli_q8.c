/*
 * heli_q8.c
 *
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * Code generation for model "heli_q8".
 *
 * Model version              : 11.51
 * Simulink Coder version : 9.4 (R2020b) 29-Jul-2020
 * C source code generated on : Thu Oct 29 12:39:38 2026
 *
 * Target selection: quarc_win64.tlc
 * Note: GRT includes extra infrastructure and instrumentation for prototyping
 * Embedded hardware selection: 32-bit Generic
 * Code generation objectives: Unspecified
 * Validation result: Not run
 */

#include "heli_q8.h"
#include "heli_q8_private.h"
#include "heli_q8_dt.h"

t_stream heli_q8_rtZt_stream = NULL;

/* Block signals (default storage) */
B_heli_q8_T heli_q8_B;

/* Continuous states */
X_heli_q8_T heli_q8_X;

/* Block states (default storage) */
DW_heli_q8_T heli_q8_DW;

/* Real-time model */
static RT_MODEL_heli_q8_T heli_q8_M_;
RT_MODEL_heli_q8_T *const heli_q8_M = &heli_q8_M_;
static void rate_scheduler(void);

/*
 * Writes out MAT-file header.  Returns success or failure.
 * Returns:
 *      0 - success
 *      1 - failure
 */
int_T rt_WriteMat4FileHeader(FILE *fp, int32_T m, int32_T n, const char *name)
{
  typedef enum { ELITTLE_ENDIAN, EBIG_ENDIAN } ByteOrder;

  int16_T one = 1;
  ByteOrder byteOrder = (*((int8_T *)&one)==1) ? ELITTLE_ENDIAN : EBIG_ENDIAN;
  int32_T type = (byteOrder == ELITTLE_ENDIAN) ? 0: 1000;
  int32_T imagf = 0;
  int32_T name_len = (int32_T)strlen(name) + 1;
  if ((fwrite(&type, sizeof(int32_T), 1, fp) == 0) ||
      (fwrite(&m, sizeof(int32_T), 1, fp) == 0) ||
      (fwrite(&n, sizeof(int32_T), 1, fp) == 0) ||
      (fwrite(&imagf, sizeof(int32_T), 1, fp) == 0) ||
      (fwrite(&name_len, sizeof(int32_T), 1, fp) == 0) ||
      (fwrite(name, sizeof(char), name_len, fp) == 0)) {
    return(1);
  } else {
    return(0);
  }
}                                      /* end rt_WriteMat4FileHeader */

/*
 *   This function updates active task flag for each subrate.
 * The function is called at model base rate, hence the
 * generated code self-manages all its subrates.
 */
static void rate_scheduler(void)
{
  /* Compute which subrates run during the next base time step.  Subrates
   * are an integer multiple of the base rate counter.  Therefore, the subtask
   * counter is reset when it reaches its limit (zero means run).
   */
  (heli_q8_M->Timing.TaskCounters.TID[2])++;
  if ((heli_q8_M->Timing.TaskCounters.TID[2]) > 4) {/* Sample time: [0.01s, 0.0s] */
    heli_q8_M->Timing.TaskCounters.TID[2] = 0;
  }

  heli_q8_M->Timing.sampleHits[2] = (heli_q8_M->Timing.TaskCounters.TID[2] == 0);
  (heli_q8_M->Timing.TaskCounters.TID[3])++;
  if ((heli_q8_M->Timing.TaskCounters.TID[3]) > 2499) {/* Sample time: [5.0s, 0.0s] */
    heli_q8_M->Timing.TaskCounters.TID[3] = 0;
  }

  heli_q8_M->Timing.sampleHits[3] = (heli_q8_M->Timing.TaskCounters.TID[3] == 0);
}

/*
 * This function updates continuous states using the ODE1 fixed-step
 * solver algorithm
 */
static void rt_ertODEUpdateContinuousStates(RTWSolverInfo *si )
{
  time_T tnew = rtsiGetSolverStopTime(si);
  time_T h = rtsiGetStepSize(si);
  real_T *x = rtsiGetContStates(si);
  ODE1_IntgData *id = (ODE1_IntgData *)rtsiGetSolverData(si);
  real_T *f0 = id->f[0];
  int_T i;
  int_T nXc = 11;
  rtsiSetSimTimeStep(si,MINOR_TIME_STEP);
  rtsiSetdX(si, f0);
  heli_q8_derivatives();
  rtsiSetT(si, tnew);
  for (i = 0; i < nXc; ++i) {
    x[i] += h * f0[i];
  }

  rtsiSetSimTimeStep(si,MAJOR_TIME_STEP);
}

/* Model output function */
void heli_q8_output(void)
{
  /* local block i/o variables */
  t_stream_ptr rtb_StreamCall1_o1;
  real_T rtb_HILReadEncoderTimebase_o1;
  real_T rtb_HILReadEncoderTimebase_o2;
  real_T rtb_HILReadEncoderTimebase_o3;
  real32_T rtb_StreamRead1_o2[10];
  int32_T rtb_StreamFormattedWrite_o2;
  int32_T rtb_StreamCall1_o3;
  real_T tmp[9];
  real_T rtb_TmpSignalConversionAtSFunct[5];
  real_T tmp_0[5];
  real_T euler_rates_tmp;
  real_T euler_rates_tmp_0;
  real_T rtb_Backgain;
  real_T rtb_Frontgain;
  int32_T i;
  int_T ci;
  if (rtmIsMajorTimeStep(heli_q8_M)) {
    /* set solver stop time */
    if (!(heli_q8_M->Timing.clockTick0+1)) {
      rtsiSetSolverStopTime(&heli_q8_M->solverInfo,
                            ((heli_q8_M->Timing.clockTickH0 + 1) *
        heli_q8_M->Timing.stepSize0 * 4294967296.0));
    } else {
      rtsiSetSolverStopTime(&heli_q8_M->solverInfo,
                            ((heli_q8_M->Timing.clockTick0 + 1) *
        heli_q8_M->Timing.stepSize0 + heli_q8_M->Timing.clockTickH0 *
        heli_q8_M->Timing.stepSize0 * 4294967296.0));
    }
  }                                    /* end MajorTimeStep */

  /* Update absolute time of base rate at minor time step */
  if (rtmIsMinorTimeStep(heli_q8_M)) {
    heli_q8_M->Timing.t[0] = rtsiGetT(&heli_q8_M->solverInfo);
  }

  if (rtmIsMajorTimeStep(heli_q8_M) &&
      heli_q8_M->Timing.TaskCounters.TID[1] == 0) {
    /* S-Function (hil_read_encoder_timebase_block): '<S4>/HIL Read Encoder Timebase' */

    /* S-Function Block: heli_q8/Heli 3D/HIL Read Encoder Timebase (hil_read_encoder_timebase_block) */
    {
      t_error result;
      result = hil_task_read_encoder(heli_q8_DW.HILReadEncoderTimebase_Task, 1,
        &heli_q8_DW.HILReadEncoderTimebase_Buffer[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(heli_q8_M, _rt_error_message);
      } else {
        rtb_HILReadEncoderTimebase_o1 =
          heli_q8_DW.HILReadEncoderTimebase_Buffer[0];
        rtb_HILReadEncoderTimebase_o2 =
          heli_q8_DW.HILReadEncoderTimebase_Buffer[1];
        rtb_HILReadEncoderTimebase_o3 =
          heli_q8_DW.HILReadEncoderTimebase_Buffer[2];
      }
    }

    /* S-Function (stream_call_block): '<S5>/Stream Call1' incorporates:
     *  Constant: '<S5>/Constant'
     *  S-Function (string_constant_block): '<S5>/String Constant'
     */

    /* S-Function Block: heli_q8/IMU1/Stream Call1 (stream_call_block) */
    {
      t_error result = 0;
      t_boolean close_flag = (heli_q8_P.Constant_Value != 0);
      rtb_StreamCall1_o1 = NULL;
      switch (heli_q8_DW.StreamCall1_State) {
       case STREAM_CALL_STATE_NOT_CONNECTED:
        {
          if (!close_flag) {
            /* Make sure URI is null-terminated */
            if (string_length((char *) heli_q8_P.StringConstant_Value, 255) ==
                255) {
              rtmSetErrorStatus(heli_q8_M,
                                "URI passed to Stream Call block is not null-terminated!");
              result = -QERR_STRING_NOT_TERMINATED;
            } else {
              result = stream_connect((char *) heli_q8_P.StringConstant_Value,
                heli_q8_P.StreamCall1_NonBlocking != 0,
                heli_q8_P.StreamCall1_SendBufferSize,
                heli_q8_P.StreamCall1_ReceiveBufferSize,
                &heli_q8_DW.StreamCall1_Stream);
              if (result == 0) {
                heli_q8_DW.StreamCall1_State = STREAM_CALL_STATE_CONNECTED;
                stream_set_byte_order(heli_q8_DW.StreamCall1_Stream,
                                      (t_stream_byte_order)
                                      heli_q8_P.StreamCall1_Endian);
                rtb_StreamCall1_o1 = &heli_q8_DW.StreamCall1_Stream;
              } else if (result == -QERR_WOULD_BLOCK) {
                heli_q8_DW.StreamCall1_State = STREAM_CALL_STATE_CONNECTING;
                result = 0;
              }
            }
          }
          break;
        }

       case STREAM_CALL_STATE_CONNECTING:
        {
          if (!close_flag) {
            const t_timeout timeout = { 0, 0, false };/* zero seconds */

            result = stream_poll(heli_q8_DW.StreamCall1_Stream, &timeout,
                                 STREAM_POLL_CONNECT);
            if (result > 0) {
              heli_q8_DW.StreamCall1_State = STREAM_CALL_STATE_CONNECTED;
              stream_set_byte_order(heli_q8_DW.StreamCall1_Stream,
                                    (t_stream_byte_order)
                                    heli_q8_P.StreamCall1_Endian);
              rtb_StreamCall1_o1 = &heli_q8_DW.StreamCall1_Stream;
              result = 0;
              break;
            } else if (result == 0) {
              break;
            }
          }

          /* Fall through deliberately */
        }

       case STREAM_CALL_STATE_CONNECTED:
        {
          rtb_StreamCall1_o1 = &heli_q8_DW.StreamCall1_Stream;
          if (!close_flag) {
            break;
          }

          /* Fall through deliberately */
        }

       default:
        {
          t_error close_result = stream_close(heli_q8_DW.StreamCall1_Stream);
          if (close_result == 0) {
            heli_q8_DW.StreamCall1_State = STREAM_CALL_STATE_NOT_CONNECTED;
            heli_q8_DW.StreamCall1_Stream = NULL;
            rtb_StreamCall1_o1 = NULL;
          } else if (result == 0) {
            result = close_result;
          }
          break;
        }
      }

      heli_q8_B.StreamCall1_o2 = heli_q8_DW.StreamCall1_State;
      rtb_StreamCall1_o3 = (int32_T) result;
    }

    /* S-Function (stream_formatted_write_block): '<S5>/Stream Formatted Write' incorporates:
     *  Constant: '<S5>/Constant1'
     */
    {
      t_error result;
      if (rtb_StreamCall1_o1 != NULL) {
        result = stream_print_utf8_char_array(*rtb_StreamCall1_o1,
          heli_q8_P.StreamFormattedWrite_MaxUnits, &rtb_StreamFormattedWrite_o2,
          "%c\n"
          , (char) heli_q8_P.Constant1_Value
          );
        if (result > 0) {
          result = stream_flush(*rtb_StreamCall1_o1);
        }

        if (result == -QERR_WOULD_BLOCK) {
          result = 0;
        }
      }
    }

    /* S-Function (stream_read_block): '<S5>/Stream Read1' incorporates:
     *  Constant: '<S5>/Constant1'
     *  S-Function (stream_call_block): '<S5>/Stream Call1'
     *  S-Function (stream_formatted_write_block): '<S5>/Stream Formatted Write'
     */

    /* S-Function Block: heli_q8/IMU1/Stream Read1 (stream_read_block) */
    {
      t_error result;
      memset(&rtb_StreamRead1_o2[0], 0, 10 * sizeof(real32_T));
      if (((t_stream_ptr)rtb_StreamCall1_o1) != NULL) {
        result = stream_receive_unit_array(*((t_stream_ptr)rtb_StreamCall1_o1),
          &rtb_StreamRead1_o2[0], sizeof(real32_T), 10);
        heli_q8_B.StreamRead1_o3 = (result > 0);
        if (result > 0 || result == -QERR_WOULD_BLOCK) {
          result = 0;
        }
      } else {
        heli_q8_B.StreamRead1_o3 = false;
        result = 0;
      }
    }

    for (i = 0; i < 10; i++) {
      /* Switch: '<S5>/Switch' */
      if (heli_q8_B.StreamRead1_o3) {
        /* Switch: '<S5>/Switch' incorporates:
         *  DataTypeConversion: '<S5>/Data Type Conversion'
         */
        heli_q8_B.Switch[i] = rtb_StreamRead1_o2[i];
      } else {
        /* Switch: '<S5>/Switch' incorporates:
         *  Memory: '<S5>/Memory'
         */
        heli_q8_B.Switch[i] = heli_q8_DW.Memory_PreviousInput[i];
      }

      /* End of Switch: '<S5>/Switch' */
    }

    for (i = 0; i < 3; i++) {
      /* Gain: '<S5>/Gain2' */
      heli_q8_B.Gain2[i] = 0.0;
      heli_q8_B.Gain2[i] += heli_q8_P.Gain2_Gain[i] * heli_q8_B.Switch[0];
      heli_q8_B.Gain2[i] += heli_q8_P.Gain2_Gain[i + 3] * heli_q8_B.Switch[1];
      heli_q8_B.Gain2[i] += heli_q8_P.Gain2_Gain[i + 6] * heli_q8_B.Switch[2];
    }

    for (i = 0; i < 3; i++) {
      /* Gain: '<S5>/Gain1' */
      heli_q8_B.Gain1[i] = 0.0;
      heli_q8_B.Gain1[i] += heli_q8_P.Gain1_Gain[i] * heli_q8_B.Switch[3];
      heli_q8_B.Gain1[i] += heli_q8_P.Gain1_Gain[i + 3] * heli_q8_B.Switch[4];
      heli_q8_B.Gain1[i] += heli_q8_P.Gain1_Gain[i + 6] * heli_q8_B.Switch[5];
    }

    /* Trigonometry: '<Root>/Atan' incorporates:
     *  Product: '<Root>/Divide'
     */
    heli_q8_B.Atan = atan(heli_q8_B.Gain2[1] / heli_q8_B.Gain2[2]);

    /* Trigonometry: '<Root>/Atan1' incorporates:
     *  Math: '<Root>/Square'
     *  Math: '<Root>/Square1'
     *  Product: '<Root>/Divide1'
     *  Sqrt: '<Root>/Square Root'
     *  Sum: '<Root>/Sum1'
     */
    heli_q8_B.Atan1 = atan(heli_q8_B.Gain2[0] / sqrt(heli_q8_B.Gain2[1] *
      heli_q8_B.Gain2[1] + heli_q8_B.Gain2[2] * heli_q8_B.Gain2[2]));

    /* MATLAB Function: '<Root>/Gyro vector to [pitch rate, elevation rate, travle rate]' incorporates:
     *  SignalConversion generated from: '<S3>/ SFunction '
     */
    /* MATLAB Function 'Gyro vector to [pitch rate, elevation rate, travle rate]': '<S3>:1' */
    /* '<S3>:1:3' */
    /* '<S3>:1:4' */
    /* '<S3>:1:8' */
    /* '<S3>:1:11' */
    rtb_Backgain = tan(heli_q8_B.Atan1);
    rtb_Frontgain = sin(heli_q8_B.Atan);
    euler_rates_tmp = cos(heli_q8_B.Atan);
    euler_rates_tmp_0 = cos(heli_q8_B.Atan1);
    tmp[0] = 1.0;
    tmp[3] = rtb_Frontgain * rtb_Backgain;
    tmp[6] = euler_rates_tmp * rtb_Backgain;
    tmp[1] = 0.0;
    tmp[4] = euler_rates_tmp;
    tmp[7] = -rtb_Frontgain;
    tmp[2] = 0.0;
    tmp[5] = rtb_Frontgain / euler_rates_tmp_0;
    tmp[8] = euler_rates_tmp / euler_rates_tmp_0;
    for (i = 0; i < 3; i++) {
      heli_q8_B.euler_rates[i] = 0.0;
      heli_q8_B.euler_rates[i] += tmp[i] * heli_q8_B.Gain1[0];
      heli_q8_B.euler_rates[i] += tmp[i + 3] * heli_q8_B.Gain1[1];
      heli_q8_B.euler_rates[i] += tmp[i + 6] * heli_q8_B.Gain1[2];
    }

    /* End of MATLAB Function: '<Root>/Gyro vector to [pitch rate, elevation rate, travle rate]' */
    /* Gain: '<S4>/Pitch: Count to rad' */
    heli_q8_B.PitchCounttorad = heli_q8_P.PitchCounttorad_Gain *
      rtb_HILReadEncoderTimebase_o2;

    /* Gain: '<S4>/Elevation: Count to rad' */
    heli_q8_B.ElevationCounttorad = heli_q8_P.ElevationCounttorad_Gain *
      rtb_HILReadEncoderTimebase_o3;
  }

  /* TransferFcn: '<S4>/Pitch: Transfer Fcn' */
  heli_q8_B.PitchTransferFcn = 0.0;
  heli_q8_B.PitchTransferFcn += heli_q8_P.PitchTransferFcn_C *
    heli_q8_X.PitchTransferFcn_CSTATE;
  heli_q8_B.PitchTransferFcn += heli_q8_P.PitchTransferFcn_D *
    heli_q8_B.PitchCounttorad;

  /* TransferFcn: '<S4>/Elevation: Transfer Fcn' */
  heli_q8_B.ElevationTransferFcn = 0.0;
  heli_q8_B.ElevationTransferFcn += heli_q8_P.ElevationTransferFcn_C *
    heli_q8_X.ElevationTransferFcn_CSTATE;
  heli_q8_B.ElevationTransferFcn += heli_q8_P.ElevationTransferFcn_D *
    heli_q8_B.ElevationCounttorad;
  if (rtmIsMajorTimeStep(heli_q8_M) &&
      heli_q8_M->Timing.TaskCounters.TID[1] == 0) {
    /* Gain: '<S4>/Travel: Count to rad' */
    heli_q8_B.TravelCounttorad = heli_q8_P.TravelCounttorad_Gain *
      rtb_HILReadEncoderTimebase_o1;
  }

  /* TransferFcn: '<S4>/Travel: Transfer Fcn' */
  heli_q8_B.TravelTransferFcn = 0.0;
  heli_q8_B.TravelTransferFcn += heli_q8_P.TravelTransferFcn_C *
    heli_q8_X.TravelTransferFcn_CSTATE;
  heli_q8_B.TravelTransferFcn += heli_q8_P.TravelTransferFcn_D *
    heli_q8_B.TravelCounttorad;
  if (rtmIsMajorTimeStep(heli_q8_M) &&
      heli_q8_M->Timing.TaskCounters.TID[1] == 0) {
    /* RateTransition: '<S6>/Rate Transition: x' */
    if (rtmIsMajorTimeStep(heli_q8_M) &&
        heli_q8_M->Timing.TaskCounters.TID[2] == 0) {
      /* RateTransition: '<S6>/Rate Transition: x' */
      heli_q8_B.RateTransitionx = heli_q8_DW.RateTransitionx_Buffer0;
    }

    /* End of RateTransition: '<S6>/Rate Transition: x' */

    /* DeadZone: '<S6>/Dead Zone: x' */
    if (heli_q8_B.RateTransitionx > heli_q8_P.DeadZonex_End) {
      rtb_Backgain = heli_q8_B.RateTransitionx - heli_q8_P.DeadZonex_End;
    } else if (heli_q8_B.RateTransitionx >= heli_q8_P.DeadZonex_Start) {
      rtb_Backgain = 0.0;
    } else {
      rtb_Backgain = heli_q8_B.RateTransitionx - heli_q8_P.DeadZonex_Start;
    }

    /* End of DeadZone: '<S6>/Dead Zone: x' */

    /* Gain: '<S6>/Joystick_gain_x' incorporates:
     *  Gain: '<S6>/Gain: x'
     */
    heli_q8_B.Joystick_gain_x = heli_q8_P.Gainx_Gain * rtb_Backgain *
      heli_q8_P.Joystick_gain_x;

    /* RateTransition: '<S6>/Rate Transition: y' */
    if (rtmIsMajorTimeStep(heli_q8_M) &&
        heli_q8_M->Timing.TaskCounters.TID[2] == 0) {
      /* RateTransition: '<S6>/Rate Transition: y' */
      heli_q8_B.RateTransitiony = heli_q8_DW.RateTransitiony_Buffer0;
    }

    /* End of RateTransition: '<S6>/Rate Transition: y' */

    /* DeadZone: '<S6>/Dead Zone: y' */
    if (heli_q8_B.RateTransitiony > heli_q8_P.DeadZoney_End) {
      rtb_Backgain = heli_q8_B.RateTransitiony - heli_q8_P.DeadZoney_End;
    } else if (heli_q8_B.RateTransitiony >= heli_q8_P.DeadZoney_Start) {
      rtb_Backgain = 0.0;
    } else {
      rtb_Backgain = heli_q8_B.RateTransitiony - heli_q8_P.DeadZoney_Start;
    }

    /* End of DeadZone: '<S6>/Dead Zone: y' */

    /* Gain: '<S6>/Joystick_gain_y' incorporates:
     *  Gain: '<S6>/Gain: y'
     */
    heli_q8_B.Joystick_gain_y = heli_q8_P.Gainy_Gain * rtb_Backgain *
      heli_q8_P.Joystick_gain_y;
  }

  /* StateSpace: '<S8>/State-Space' */
  for (i = 0; i < 5; i++) {
    heli_q8_B.StateSpace[i] = 0.0;
    for (ci = 0; ci < 5; ci++) {
      heli_q8_B.StateSpace[i] += heli_q8_P.C_est[ci * 5 + i] *
        heli_q8_X.StateSpace_CSTATE[ci];
    }
  }

  /* End of StateSpace: '<S8>/State-Space' */
  if (rtmIsMajorTimeStep(heli_q8_M) &&
      heli_q8_M->Timing.TaskCounters.TID[1] == 0) {
    /* SignalConversion generated from: '<Root>/To File' */
    heli_q8_B.TmpSignalConversionAtToFileInpo[0] = heli_q8_B.Joystick_gain_x;
    heli_q8_B.TmpSignalConversionAtToFileInpo[1] = heli_q8_B.PitchCounttorad;
    heli_q8_B.TmpSignalConversionAtToFileInpo[2] = heli_q8_B.PitchTransferFcn;
    heli_q8_B.TmpSignalConversionAtToFileInpo[3] =
      heli_q8_B.ElevationTransferFcn;
    heli_q8_B.TmpSignalConversionAtToFileInpo[4] = heli_q8_B.ElevationCounttorad;
    heli_q8_B.TmpSignalConversionAtToFileInpo[5] = heli_q8_B.Joystick_gain_y;
    heli_q8_B.TmpSignalConversionAtToFileInpo[8] = heli_q8_B.StateSpace[3];
    heli_q8_B.TmpSignalConversionAtToFileInpo[9] = heli_q8_B.StateSpace[2];
    heli_q8_B.TmpSignalConversionAtToFileInpo[10] = heli_q8_B.Atan;
    heli_q8_B.TmpSignalConversionAtToFileInpo[6] = heli_q8_B.StateSpace[0];
    heli_q8_B.TmpSignalConversionAtToFileInpo[11] = heli_q8_B.euler_rates[0];
    heli_q8_B.TmpSignalConversionAtToFileInpo[7] = heli_q8_B.StateSpace[1];
    heli_q8_B.TmpSignalConversionAtToFileInpo[12] = heli_q8_B.euler_rates[1];
    heli_q8_B.TmpSignalConversionAtToFileInpo[13] = heli_q8_B.Atan1;
    heli_q8_B.TmpSignalConversionAtToFileInpo[14] = 0.0;

    /* ToFile: '<Root>/To File' */
    {
      if (!(++heli_q8_DW.ToFile_IWORK.Decimation % 1) &&
          (heli_q8_DW.ToFile_IWORK.Count * (15 + 1)) + 1 < 100000000 ) {
        FILE *fp = (FILE *) heli_q8_DW.ToFile_PWORK.FilePtr;
        if (fp != (NULL)) {
          real_T u[15 + 1];
          heli_q8_DW.ToFile_IWORK.Decimation = 0;
          u[0] = heli_q8_M->Timing.t[1];
          u[1] = heli_q8_B.TmpSignalConversionAtToFileInpo[0];
          u[2] = heli_q8_B.TmpSignalConversionAtToFileInpo[1];
          u[3] = heli_q8_B.TmpSignalConversionAtToFileInpo[2];
          u[4] = heli_q8_B.TmpSignalConversionAtToFileInpo[3];
          u[5] = heli_q8_B.TmpSignalConversionAtToFileInpo[4];
          u[6] = heli_q8_B.TmpSignalConversionAtToFileInpo[5];
          u[7] = heli_q8_B.TmpSignalConversionAtToFileInpo[6];
          u[8] = heli_q8_B.TmpSignalConversionAtToFileInpo[7];
          u[9] = heli_q8_B.TmpSignalConversionAtToFileInpo[8];
          u[10] = heli_q8_B.TmpSignalConversionAtToFileInpo[9];
          u[11] = heli_q8_B.TmpSignalConversionAtToFileInpo[10];
          u[12] = heli_q8_B.TmpSignalConversionAtToFileInpo[11];
          u[13] = heli_q8_B.TmpSignalConversionAtToFileInpo[12];
          u[14] = heli_q8_B.TmpSignalConversionAtToFileInpo[13];
          u[15] = heli_q8_B.TmpSignalConversionAtToFileInpo[14];
          if (fwrite(u, sizeof(real_T), 15 + 1, fp) != 15 + 1) {
            rtmSetErrorStatus(heli_q8_M,
                              "Error writing to MAT-file tempDataFile.mat");
            return;
          }

          if (((++heli_q8_DW.ToFile_IWORK.Count) * (15 + 1))+1 >= 100000000) {
            (void)fprintf(stdout,
                          "*** The ToFile block will stop logging data before\n"
                          "    the simulation has ended, because it has reached\n"
                          "    the maximum number of elements (100000000)\n"
                          "    allowed in MAT-file tempDataFile.mat.\n");
          }
        }
      }
    }
  }

  /* Sum: '<Root>/Add' incorporates:
   *  Constant: '<Root>/Constant1'
   */
  heli_q8_B.Add = heli_q8_B.StateSpace[2] + heli_q8_P.Constant1_Value_g;
  if (rtmIsMajorTimeStep(heli_q8_M) &&
      heli_q8_M->Timing.TaskCounters.TID[1] == 0) {
    /* Sum: '<Root>/Add1' incorporates:
     *  Constant: '<Root>/Constant1'
     */
    heli_q8_B.Add1 = heli_q8_P.Constant1_Value_g + heli_q8_B.Atan1;

    /* Gain: '<S7>/Gain' incorporates:
     *  SignalConversion generated from: '<S7>/Gain'
     */
    heli_q8_B.Gain[0] = 0.0;
    heli_q8_B.Gain[0] += heli_q8_P.F[0] * heli_q8_B.Joystick_gain_x;
    heli_q8_B.Gain[0] += heli_q8_P.F[2] * heli_q8_B.Joystick_gain_y;
    heli_q8_B.Gain[1] = 0.0;
    heli_q8_B.Gain[1] += heli_q8_P.F[1] * heli_q8_B.Joystick_gain_x;
    heli_q8_B.Gain[1] += heli_q8_P.F[3] * heli_q8_B.Joystick_gain_y;
  }

  /* Integrator: '<S7>/Integrator1' */
  heli_q8_B.Integrator1 = heli_q8_X.Integrator1_CSTATE;

  /* Sum: '<S7>/Sum3' incorporates:
   *  Constant: '<S7>/Constant'
   *  Integrator: '<S7>/Integrator'
   */
  heli_q8_B.Sum3 = heli_q8_P.Constant_Value_f + heli_q8_X.Integrator_CSTATE;

  /* SignalConversion generated from: '<S7>/Gain1' */
  tmp_0[0] = heli_q8_B.StateSpace[0];
  tmp_0[1] = heli_q8_B.StateSpace[1];
  tmp_0[2] = heli_q8_B.StateSpace[3];
  tmp_0[3] = heli_q8_B.Integrator1;
  tmp_0[4] = heli_q8_B.Sum3;
  for (i = 0; i < 2; i++) {
    /* Sum: '<S7>/Sum' incorporates:
     *  Gain: '<S7>/Gain1'
     */
    rtb_Backgain = 0.0;
    for (ci = 0; ci < 5; ci++) {
      rtb_Backgain += heli_q8_P.K[(ci << 1) + i] * tmp_0[ci];
    }

    heli_q8_B.Sum[i] = heli_q8_B.Gain[i] - rtb_Backgain;

    /* End of Sum: '<S7>/Sum' */
  }

  /* Sum: '<Root>/Sum' incorporates:
   *  Constant: '<Root>/Constant3'
   */
  rtb_Backgain = heli_q8_B.Sum[0] + heli_q8_P.v_s0;

  /* Sum: '<S1>/Add' */
  rtb_Frontgain = rtb_Backgain - heli_q8_B.Sum[1];

  /* Sum: '<S1>/Subtract' */
  rtb_Backgain += heli_q8_B.Sum[1];

  /* Gain: '<S1>/Back gain' */
  rtb_Backgain *= heli_q8_P.Backgain_Gain;

  /* Gain: '<S1>/Front gain' */
  rtb_Frontgain *= heli_q8_P.Frontgain_Gain;
  if (rtmIsMajorTimeStep(heli_q8_M) &&
      heli_q8_M->Timing.TaskCounters.TID[1] == 0) {
  }

  /* Saturate: '<S4>/Front motor: Saturation' */
  if (rtb_Frontgain > heli_q8_P.FrontmotorSaturation_UpperSat) {
    /* Saturate: '<S4>/Front motor: Saturation' */
    heli_q8_B.FrontmotorSaturation = heli_q8_P.FrontmotorSaturation_UpperSat;
  } else if (rtb_Frontgain < heli_q8_P.FrontmotorSaturation_LowerSat) {
    /* Saturate: '<S4>/Front motor: Saturation' */
    heli_q8_B.FrontmotorSaturation = heli_q8_P.FrontmotorSaturation_LowerSat;
  } else {
    /* Saturate: '<S4>/Front motor: Saturation' */
    heli_q8_B.FrontmotorSaturation = rtb_Frontgain;
  }

  /* End of Saturate: '<S4>/Front motor: Saturation' */

  /* Saturate: '<S4>/Back motor: Saturation' */
  if (rtb_Backgain > heli_q8_P.BackmotorSaturation_UpperSat) {
    /* Saturate: '<S4>/Back motor: Saturation' */
    heli_q8_B.BackmotorSaturation = heli_q8_P.BackmotorSaturation_UpperSat;
  } else if (rtb_Backgain < heli_q8_P.BackmotorSaturation_LowerSat) {
    /* Saturate: '<S4>/Back motor: Saturation' */
    heli_q8_B.BackmotorSaturation = heli_q8_P.BackmotorSaturation_LowerSat;
  } else {
    /* Saturate: '<S4>/Back motor: Saturation' */
    heli_q8_B.BackmotorSaturation = rtb_Backgain;
  }

  /* End of Saturate: '<S4>/Back motor: Saturation' */
  if (rtmIsMajorTimeStep(heli_q8_M) &&
      heli_q8_M->Timing.TaskCounters.TID[1] == 0) {
    /* S-Function (hil_write_analog_block): '<S4>/HIL Write Analog' */

    /* S-Function Block: heli_q8/Heli 3D/HIL Write Analog (hil_write_analog_block) */
    {
      t_error result;
      heli_q8_DW.HILWriteAnalog_Buffer[0] = heli_q8_B.FrontmotorSaturation;
      heli_q8_DW.HILWriteAnalog_Buffer[1] = heli_q8_B.BackmotorSaturation;
      result = hil_write_analog(heli_q8_DW.HILInitialize_Card,
        heli_q8_P.HILWriteAnalog_channels, 2, &heli_q8_DW.HILWriteAnalog_Buffer
        [0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(heli_q8_M, _rt_error_message);
      }
    }

    /* S-Function (stop_with_error_block): '<S5>/Stop with Call Error' */

    /* S-Function Block: heli_q8/IMU1/Stop with Call Error (stop_with_error_block) */
    {
      if (rtb_StreamCall1_o3 < 0) {
        msg_get_error_messageA(NULL, rtb_StreamCall1_o3, _rt_error_message,
          sizeof(_rt_error_message));
        rtmSetErrorStatus(heli_q8_M, _rt_error_message);
        return;
      }
    }
  }

  if (rtmIsMajorTimeStep(heli_q8_M) &&
      heli_q8_M->Timing.TaskCounters.TID[2] == 0) {
    /* S-Function (game_controller_block): '<S6>/Game Controller' */

    /* S-Function Block: heli_q8/Joystick/Game Controller (game_controller_block) */
    {
      if (heli_q8_P.GameController_Enabled) {
        t_game_controller_states state;
        t_boolean new_data;
        t_error result;
        result = game_controller_poll(heli_q8_DW.GameController_Controller,
          &state, &new_data);
        if (result < 0) {
          new_data = false;
        }

        heli_q8_B.GameController_o4 = state.x;
        heli_q8_B.GameController_o5 = state.y;
      } else {
        heli_q8_B.GameController_o4 = 0;
        heli_q8_B.GameController_o5 = 0;
      }
    }
  }

  if (rtmIsMajorTimeStep(heli_q8_M) &&
      heli_q8_M->Timing.TaskCounters.TID[1] == 0) {
  }

  /* Sum: '<S7>/Sum1' */
  heli_q8_B.Sum1 = heli_q8_B.Joystick_gain_y - heli_q8_B.StateSpace[3];

  /* Sum: '<S7>/Sum2' */
  heli_q8_B.Sum2 = heli_q8_B.Joystick_gain_x - heli_q8_B.StateSpace[0];
  if (rtmIsMajorTimeStep(heli_q8_M) &&
      heli_q8_M->Timing.TaskCounters.TID[1] == 0) {
    /* SignalConversion generated from: '<S13>/ SFunction ' incorporates:
     *  MATLAB Function: '<S8>/MATLAB Function'
     */
    rtb_TmpSignalConversionAtSFunct[0] = heli_q8_B.Atan;
    rtb_TmpSignalConversionAtSFunct[1] = heli_q8_B.Atan1;
    rtb_TmpSignalConversionAtSFunct[2] = heli_q8_B.euler_rates[0];
    rtb_TmpSignalConversionAtSFunct[3] = heli_q8_B.euler_rates[1];
    rtb_TmpSignalConversionAtSFunct[4] = heli_q8_B.euler_rates[2];

    /* MATLAB Function: '<S8>/MATLAB Function' */
    /* MATLAB Function 'Luenberger/MATLAB Function': '<S13>:1' */
    /* '<S13>:1:3' */
    for (i = 0; i < 5; i++) {
      rtb_Backgain = rtb_TmpSignalConversionAtSFunct[i];
      heli_q8_B.y[i] = rtb_Backgain;
      if (rtIsNaN(rtb_Backgain) || rtIsInf(rtb_Backgain)) {
        /* '<S13>:1:4' */
        heli_q8_B.y[i] = 0.0;
      }
    }
  }

  /* SignalConversion generated from: '<S8>/State-Space' */
  heli_q8_B.TmpSignalConversionAtStateSpace[2] = heli_q8_B.y[0];
  heli_q8_B.TmpSignalConversionAtStateSpace[3] = heli_q8_B.y[2];
  heli_q8_B.TmpSignalConversionAtStateSpace[4] = heli_q8_B.y[1];
  heli_q8_B.TmpSignalConversionAtStateSpace[0] = heli_q8_B.Sum[0];
  heli_q8_B.TmpSignalConversionAtStateSpace[5] = heli_q8_B.y[3];
  heli_q8_B.TmpSignalConversionAtStateSpace[1] = heli_q8_B.Sum[1];
  heli_q8_B.TmpSignalConversionAtStateSpace[6] = heli_q8_B.y[4];

  /* Integrator: '<S12>/Integrator' */
  /* Limited  Integrator  */
  if (heli_q8_X.Integrator_CSTATE_n >= heli_q8_P.Integrator_UpperSat) {
    heli_q8_X.Integrator_CSTATE_n = heli_q8_P.Integrator_UpperSat;
  } else {
    if (heli_q8_X.Integrator_CSTATE_n <= heli_q8_P.Integrator_LowerSat) {
      heli_q8_X.Integrator_CSTATE_n = heli_q8_P.Integrator_LowerSat;
    }
  }

  /* End of Integrator: '<S12>/Integrator' */
  if (rtmIsMajorTimeStep(heli_q8_M) &&
      heli_q8_M->Timing.TaskCounters.TID[1] == 0) {
    /* Gain: '<S12>/K_ei' incorporates:
     *  Constant: '<Root>/Constant'
     */
    heli_q8_B.K_ei = heli_q8_P.K_ei_Gain * heli_q8_P.Constant_Value_n;

    /* Gain: '<S9>/Gain1' incorporates:
     *  Sum: '<S9>/Sum'
     */
    heli_q8_B.Gain1_o = heli_q8_P.k_pp * 0.0;

    /* Gain: '<S9>/Gain' */
    heli_q8_B.Gain_b = heli_q8_P.k_pd * 0.0;
  }
}

/* Model update function */
void heli_q8_update(void)
{
  if (rtmIsMajorTimeStep(heli_q8_M) &&
      heli_q8_M->Timing.TaskCounters.TID[1] == 0) {
    /* Update for Memory: '<S5>/Memory' */
    memcpy(&heli_q8_DW.Memory_PreviousInput[0], &heli_q8_B.Switch[0], 10U *
           sizeof(real_T));
  }

  /* Update for RateTransition: '<S6>/Rate Transition: x' */
  if (rtmIsMajorTimeStep(heli_q8_M) &&
      heli_q8_M->Timing.TaskCounters.TID[2] == 0) {
    heli_q8_DW.RateTransitionx_Buffer0 = heli_q8_B.GameController_o4;

    /* Update for RateTransition: '<S6>/Rate Transition: y' */
    heli_q8_DW.RateTransitiony_Buffer0 = heli_q8_B.GameController_o5;
  }

  /* End of Update for RateTransition: '<S6>/Rate Transition: x' */
  if (rtmIsMajorTimeStep(heli_q8_M)) {
    rt_ertODEUpdateContinuousStates(&heli_q8_M->solverInfo);
  }

  /* Update absolute time for base rate */
  /* The "clockTick0" counts the number of times the code of this task has
   * been executed. The absolute time is the multiplication of "clockTick0"
   * and "Timing.stepSize0". Size of "clockTick0" ensures timer will not
   * overflow during the application lifespan selected.
   * Timer of this task consists of two 32 bit unsigned integers.
   * The two integers represent the low bits Timing.clockTick0 and the high bits
   * Timing.clockTickH0. When the low bit overflows to 0, the high bits increment.
   */
  if (!(++heli_q8_M->Timing.clockTick0)) {
    ++heli_q8_M->Timing.clockTickH0;
  }

  heli_q8_M->Timing.t[0] = rtsiGetSolverStopTime(&heli_q8_M->solverInfo);

  {
    /* Update absolute timer for sample time: [0.002s, 0.0s] */
    /* The "clockTick1" counts the number of times the code of this task has
     * been executed. The absolute time is the multiplication of "clockTick1"
     * and "Timing.stepSize1". Size of "clockTick1" ensures timer will not
     * overflow during the application lifespan selected.
     * Timer of this task consists of two 32 bit unsigned integers.
     * The two integers represent the low bits Timing.clockTick1 and the high bits
     * Timing.clockTickH1. When the low bit overflows to 0, the high bits increment.
     */
    if (!(++heli_q8_M->Timing.clockTick1)) {
      ++heli_q8_M->Timing.clockTickH1;
    }

    heli_q8_M->Timing.t[1] = heli_q8_M->Timing.clockTick1 *
      heli_q8_M->Timing.stepSize1 + heli_q8_M->Timing.clockTickH1 *
      heli_q8_M->Timing.stepSize1 * 4294967296.0;
  }

  if (rtmIsMajorTimeStep(heli_q8_M) &&
      heli_q8_M->Timing.TaskCounters.TID[2] == 0) {
    /* Update absolute timer for sample time: [0.01s, 0.0s] */
    /* The "clockTick2" counts the number of times the code of this task has
     * been executed. The absolute time is the multiplication of "clockTick2"
     * and "Timing.stepSize2". Size of "clockTick2" ensures timer will not
     * overflow during the application lifespan selected.
     * Timer of this task consists of two 32 bit unsigned integers.
     * The two integers represent the low bits Timing.clockTick2 and the high bits
     * Timing.clockTickH2. When the low bit overflows to 0, the high bits increment.
     */
    if (!(++heli_q8_M->Timing.clockTick2)) {
      ++heli_q8_M->Timing.clockTickH2;
    }

    heli_q8_M->Timing.t[2] = heli_q8_M->Timing.clockTick2 *
      heli_q8_M->Timing.stepSize2 + heli_q8_M->Timing.clockTickH2 *
      heli_q8_M->Timing.stepSize2 * 4294967296.0;
  }

  if (rtmIsMajorTimeStep(heli_q8_M) &&
      heli_q8_M->Timing.TaskCounters.TID[3] == 0) {
    /* Update absolute timer for sample time: [5.0s, 0.0s] */
    /* The "clockTick3" counts the number of times the code of this task has
     * been executed. The absolute time is the multiplication of "clockTick3"
     * and "Timing.stepSize3". Size of "clockTick3" ensures timer will not
     * overflow during the application lifespan selected.
     * Timer of this task consists of two 32 bit unsigned integers.
     * The two integers represent the low bits Timing.clockTick3 and the high bits
     * Timing.clockTickH3. When the low bit overflows to 0, the high bits increment.
     */
    if (!(++heli_q8_M->Timing.clockTick3)) {
      ++heli_q8_M->Timing.clockTickH3;
    }

    heli_q8_M->Timing.t[3] = heli_q8_M->Timing.clockTick3 *
      heli_q8_M->Timing.stepSize3 + heli_q8_M->Timing.clockTickH3 *
      heli_q8_M->Timing.stepSize3 * 4294967296.0;
  }

  rate_scheduler();
}

/* Derivatives for root system: '<Root>' */
void heli_q8_derivatives(void)
{
  XDot_heli_q8_T *_rtXdot;
  int_T is;
  int_T ri;
  boolean_T lsat;
  boolean_T usat;
  _rtXdot = ((XDot_heli_q8_T *) heli_q8_M->derivs);

  /* Derivatives for TransferFcn: '<S4>/Pitch: Transfer Fcn' */
  _rtXdot->PitchTransferFcn_CSTATE = 0.0;
  _rtXdot->PitchTransferFcn_CSTATE += heli_q8_P.PitchTransferFcn_A *
    heli_q8_X.PitchTransferFcn_CSTATE;
  _rtXdot->PitchTransferFcn_CSTATE += heli_q8_B.PitchCounttorad;

  /* Derivatives for TransferFcn: '<S4>/Elevation: Transfer Fcn' */
  _rtXdot->ElevationTransferFcn_CSTATE = 0.0;
  _rtXdot->ElevationTransferFcn_CSTATE += heli_q8_P.ElevationTransferFcn_A *
    heli_q8_X.ElevationTransferFcn_CSTATE;
  _rtXdot->ElevationTransferFcn_CSTATE += heli_q8_B.ElevationCounttorad;

  /* Derivatives for TransferFcn: '<S4>/Travel: Transfer Fcn' */
  _rtXdot->TravelTransferFcn_CSTATE = 0.0;
  _rtXdot->TravelTransferFcn_CSTATE += heli_q8_P.TravelTransferFcn_A *
    heli_q8_X.TravelTransferFcn_CSTATE;
  _rtXdot->TravelTransferFcn_CSTATE += heli_q8_B.TravelCounttorad;

  /* Derivatives for StateSpace: '<S8>/State-Space' */
  for (is = 0; is < 5; is++) {
    _rtXdot->StateSpace_CSTATE[is] = 0.0;
  }

  for (ri = 0; ri < 5; ri++) {
    for (is = 0; is < 5; is++) {
      _rtXdot->StateSpace_CSTATE[ri] += heli_q8_P.A_est[is * 5 + ri] *
        heli_q8_X.StateSpace_CSTATE[is];
    }

    for (is = 0; is < 7; is++) {
      _rtXdot->StateSpace_CSTATE[ri] += heli_q8_P.B_est[is * 5 + ri] *
        heli_q8_B.TmpSignalConversionAtStateSpace[is];
    }
  }

  /* End of Derivatives for StateSpace: '<S8>/State-Space' */

  /* Derivatives for Integrator: '<S7>/Integrator1' */
  _rtXdot->Integrator1_CSTATE = heli_q8_B.Sum2;

  /* Derivatives for Integrator: '<S7>/Integrator' */
  _rtXdot->Integrator_CSTATE = heli_q8_B.Sum1;

  /* Derivatives for Integrator: '<S12>/Integrator' */
  lsat = (heli_q8_X.Integrator_CSTATE_n <= heli_q8_P.Integrator_LowerSat);
  usat = (heli_q8_X.Integrator_CSTATE_n >= heli_q8_P.Integrator_UpperSat);
  if (((!lsat) && (!usat)) || (lsat && (heli_q8_B.K_ei > 0.0)) || (usat &&
       (heli_q8_B.K_ei < 0.0))) {
    _rtXdot->Integrator_CSTATE_n = heli_q8_B.K_ei;
  } else {
    /* in saturation */
    _rtXdot->Integrator_CSTATE_n = 0.0;
  }

  /* End of Derivatives for Integrator: '<S12>/Integrator' */
}

/* Model initialize function */
void heli_q8_initialize(void)
{
  /* Start for S-Function (hil_initialize_block): '<Root>/HIL Initialize' */

  /* S-Function Block: heli_q8/HIL Initialize (hil_initialize_block) */
  {
    t_int result;
    t_boolean is_switching;
    result = hil_open("q8_usb", "0", &heli_q8_DW.HILInitialize_Card);
    if (result < 0) {
      msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
        (_rt_error_message));
      rtmSetErrorStatus(heli_q8_M, _rt_error_message);
      return;
    }

    is_switching = false;
    result = hil_set_card_specific_options(heli_q8_DW.HILInitialize_Card,
      "update_rate=normal;decimation=1", 32);
    if (result < 0) {
      msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
        (_rt_error_message));
      rtmSetErrorStatus(heli_q8_M, _rt_error_message);
      return;
    }

    result = hil_watchdog_clear(heli_q8_DW.HILInitialize_Card);
    if (result < 0 && result != -QERR_HIL_WATCHDOG_CLEAR) {
      msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
        (_rt_error_message));
      rtmSetErrorStatus(heli_q8_M, _rt_error_message);
      return;
    }

    if ((heli_q8_P.HILInitialize_AIPStart && !is_switching) ||
        (heli_q8_P.HILInitialize_AIPEnter && is_switching)) {
      {
        int_T i1;
        real_T *dw_AIMinimums = &heli_q8_DW.HILInitialize_AIMinimums[0];
        for (i1=0; i1 < 8; i1++) {
          dw_AIMinimums[i1] = (heli_q8_P.HILInitialize_AILow);
        }
      }

      {
        int_T i1;
        real_T *dw_AIMaximums = &heli_q8_DW.HILInitialize_AIMaximums[0];
        for (i1=0; i1 < 8; i1++) {
          dw_AIMaximums[i1] = heli_q8_P.HILInitialize_AIHigh;
        }
      }

      result = hil_set_analog_input_ranges(heli_q8_DW.HILInitialize_Card,
        heli_q8_P.HILInitialize_AIChannels, 8U,
        &heli_q8_DW.HILInitialize_AIMinimums[0],
        &heli_q8_DW.HILInitialize_AIMaximums[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(heli_q8_M, _rt_error_message);
        return;
      }
    }

    if ((heli_q8_P.HILInitialize_AOPStart && !is_switching) ||
        (heli_q8_P.HILInitialize_AOPEnter && is_switching)) {
      {
        int_T i1;
        real_T *dw_AOMinimums = &heli_q8_DW.HILInitialize_AOMinimums[0];
        for (i1=0; i1 < 8; i1++) {
          dw_AOMinimums[i1] = (heli_q8_P.HILInitialize_AOLow);
        }
      }

      {
        int_T i1;
        real_T *dw_AOMaximums = &heli_q8_DW.HILInitialize_AOMaximums[0];
        for (i1=0; i1 < 8; i1++) {
          dw_AOMaximums[i1] = heli_q8_P.HILInitialize_AOHigh;
        }
      }

      result = hil_set_analog_output_ranges(heli_q8_DW.HILInitialize_Card,
        heli_q8_P.HILInitialize_AOChannels, 8U,
        &heli_q8_DW.HILInitialize_AOMinimums[0],
        &heli_q8_DW.HILInitialize_AOMaximums[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(heli_q8_M, _rt_error_message);
        return;
      }
    }

    if ((heli_q8_P.HILInitialize_AOStart && !is_switching) ||
        (heli_q8_P.HILInitialize_AOEnter && is_switching)) {
      {
        int_T i1;
        real_T *dw_AOVoltages = &heli_q8_DW.HILInitialize_AOVoltages[0];
        for (i1=0; i1 < 8; i1++) {
          dw_AOVoltages[i1] = heli_q8_P.HILInitialize_AOInitial;
        }
      }

      result = hil_write_analog(heli_q8_DW.HILInitialize_Card,
        heli_q8_P.HILInitialize_AOChannels, 8U,
        &heli_q8_DW.HILInitialize_AOVoltages[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(heli_q8_M, _rt_error_message);
        return;
      }
    }

    if (heli_q8_P.HILInitialize_AOReset) {
      {
        int_T i1;
        real_T *dw_AOVoltages = &heli_q8_DW.HILInitialize_AOVoltages[0];
        for (i1=0; i1 < 8; i1++) {
          dw_AOVoltages[i1] = heli_q8_P.HILInitialize_AOWatchdog;
        }
      }

      result = hil_watchdog_set_analog_expiration_state
        (heli_q8_DW.HILInitialize_Card, heli_q8_P.HILInitialize_AOChannels, 8U,
         &heli_q8_DW.HILInitialize_AOVoltages[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(heli_q8_M, _rt_error_message);
        return;
      }
    }

    if ((heli_q8_P.HILInitialize_EIPStart && !is_switching) ||
        (heli_q8_P.HILInitialize_EIPEnter && is_switching)) {
      {
        int_T i1;
        int32_T *dw_QuadratureModes = &heli_q8_DW.HILInitialize_QuadratureModes
          [0];
        for (i1=0; i1 < 8; i1++) {
          dw_QuadratureModes[i1] = heli_q8_P.HILInitialize_EIQuadrature;
        }
      }

      result = hil_set_encoder_quadrature_mode(heli_q8_DW.HILInitialize_Card,
        heli_q8_P.HILInitialize_EIChannels, 8U, (t_encoder_quadrature_mode *)
        &heli_q8_DW.HILInitialize_QuadratureModes[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(heli_q8_M, _rt_error_message);
        return;
      }
    }

    if ((heli_q8_P.HILInitialize_EIStart && !is_switching) ||
        (heli_q8_P.HILInitialize_EIEnter && is_switching)) {
      {
        int_T i1;
        int32_T *dw_InitialEICounts = &heli_q8_DW.HILInitialize_InitialEICounts
          [0];
        for (i1=0; i1 < 8; i1++) {
          dw_InitialEICounts[i1] = heli_q8_P.HILInitialize_EIInitial;
        }
      }

      result = hil_set_encoder_counts(heli_q8_DW.HILInitialize_Card,
        heli_q8_P.HILInitialize_EIChannels, 8U,
        &heli_q8_DW.HILInitialize_InitialEICounts[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(heli_q8_M, _rt_error_message);
        return;
      }
    }

    if ((heli_q8_P.HILInitialize_POPStart && !is_switching) ||
        (heli_q8_P.HILInitialize_POPEnter && is_switching)) {
      uint32_T num_duty_cycle_modes = 0;
      uint32_T num_frequency_modes = 0;

      {
        int_T i1;
        int32_T *dw_POModeValues = &heli_q8_DW.HILInitialize_POModeValues[0];
        for (i1=0; i1 < 8; i1++) {
          dw_POModeValues[i1] = heli_q8_P.HILInitialize_POModes;
        }
      }

      result = hil_set_pwm_mode(heli_q8_DW.HILInitialize_Card,
        heli_q8_P.HILInitialize_POChannels, 8U, (t_pwm_mode *)
        &heli_q8_DW.HILInitialize_POModeValues[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(heli_q8_M, _rt_error_message);
        return;
      }

      {
        int_T i1;
        const uint32_T *p_HILInitialize_POChannels =
          heli_q8_P.HILInitialize_POChannels;
        int32_T *dw_POModeValues = &heli_q8_DW.HILInitialize_POModeValues[0];
        for (i1=0; i1 < 8; i1++) {
          if (dw_POModeValues[i1] == PWM_DUTY_CYCLE_MODE || dw_POModeValues[i1] ==
              PWM_ONE_SHOT_MODE || dw_POModeValues[i1] == PWM_TIME_MODE ||
              dw_POModeValues[i1] == PWM_RAW_MODE) {
            heli_q8_DW.HILInitialize_POSortedChans[num_duty_cycle_modes] =
              (p_HILInitialize_POChannels[i1]);
            heli_q8_DW.HILInitialize_POSortedFreqs[num_duty_cycle_modes] =
              heli_q8_P.HILInitialize_POFrequency;
            num_duty_cycle_modes++;
          } else {
            heli_q8_DW.HILInitialize_POSortedChans[7U - num_frequency_modes] =
              (p_HILInitialize_POChannels[i1]);
            heli_q8_DW.HILInitialize_POSortedFreqs[7U - num_frequency_modes] =
              heli_q8_P.HILInitialize_POFrequency;
            num_frequency_modes++;
          }
        }
      }

      if (num_duty_cycle_modes > 0) {
        result = hil_set_pwm_frequency(heli_q8_DW.HILInitialize_Card,
          &heli_q8_DW.HILInitialize_POSortedChans[0], num_duty_cycle_modes,
          &heli_q8_DW.HILInitialize_POSortedFreqs[0]);
        if (result < 0) {
          msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
            (_rt_error_message));
          rtmSetErrorStatus(heli_q8_M, _rt_error_message);
          return;
        }
      }

      if (num_frequency_modes > 0) {
        result = hil_set_pwm_duty_cycle(heli_q8_DW.HILInitialize_Card,
          &heli_q8_DW.HILInitialize_POSortedChans[num_duty_cycle_modes],
          num_frequency_modes,
          &heli_q8_DW.HILInitialize_POSortedFreqs[num_duty_cycle_modes]);
        if (result < 0) {
          msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
            (_rt_error_message));
          rtmSetErrorStatus(heli_q8_M, _rt_error_message);
          return;
        }
      }

      {
        int_T i1;
        int32_T *dw_POModeValues = &heli_q8_DW.HILInitialize_POModeValues[0];
        for (i1=0; i1 < 8; i1++) {
          dw_POModeValues[i1] = heli_q8_P.HILInitialize_POConfiguration;
        }
      }

      {
        int_T i1;
        int32_T *dw_POAlignValues = &heli_q8_DW.HILInitialize_POAlignValues[0];
        for (i1=0; i1 < 8; i1++) {
          dw_POAlignValues[i1] = heli_q8_P.HILInitialize_POAlignment;
        }
      }

      {
        int_T i1;
        int32_T *dw_POPolarityVals = &heli_q8_DW.HILInitialize_POPolarityVals[0];
        for (i1=0; i1 < 8; i1++) {
          dw_POPolarityVals[i1] = heli_q8_P.HILInitialize_POPolarity;
        }
      }

      result = hil_set_pwm_configuration(heli_q8_DW.HILInitialize_Card,
        heli_q8_P.HILInitialize_POChannels, 8U,
        (t_pwm_configuration *) &heli_q8_DW.HILInitialize_POModeValues[0],
        (t_pwm_alignment *) &heli_q8_DW.HILInitialize_POAlignValues[0],
        (t_pwm_polarity *) &heli_q8_DW.HILInitialize_POPolarityVals[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(heli_q8_M, _rt_error_message);
        return;
      }

      {
        int_T i1;
        real_T *dw_POSortedFreqs = &heli_q8_DW.HILInitialize_POSortedFreqs[0];
        for (i1=0; i1 < 8; i1++) {
          dw_POSortedFreqs[i1] = heli_q8_P.HILInitialize_POLeading;
        }
      }

      {
        int_T i1;
        real_T *dw_POValues = &heli_q8_DW.HILInitialize_POValues[0];
        for (i1=0; i1 < 8; i1++) {
          dw_POValues[i1] = heli_q8_P.HILInitialize_POTrailing;
        }
      }

      result = hil_set_pwm_deadband(heli_q8_DW.HILInitialize_Card,
        heli_q8_P.HILInitialize_POChannels, 8U,
        &heli_q8_DW.HILInitialize_POSortedFreqs[0],
        &heli_q8_DW.HILInitialize_POValues[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(heli_q8_M, _rt_error_message);
        return;
      }
    }

    if ((heli_q8_P.HILInitialize_POStart && !is_switching) ||
        (heli_q8_P.HILInitialize_POEnter && is_switching)) {
      {
        int_T i1;
        real_T *dw_POValues = &heli_q8_DW.HILInitialize_POValues[0];
        for (i1=0; i1 < 8; i1++) {
          dw_POValues[i1] = heli_q8_P.HILInitialize_POInitial;
        }
      }

      result = hil_write_pwm(heli_q8_DW.HILInitialize_Card,
        heli_q8_P.HILInitialize_POChannels, 8U,
        &heli_q8_DW.HILInitialize_POValues[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(heli_q8_M, _rt_error_message);
        return;
      }
    }

    if (heli_q8_P.HILInitialize_POReset) {
      {
        int_T i1;
        real_T *dw_POValues = &heli_q8_DW.HILInitialize_POValues[0];
        for (i1=0; i1 < 8; i1++) {
          dw_POValues[i1] = heli_q8_P.HILInitialize_POWatchdog;
        }
      }

      result = hil_watchdog_set_pwm_expiration_state
        (heli_q8_DW.HILInitialize_Card, heli_q8_P.HILInitialize_POChannels, 8U,
         &heli_q8_DW.HILInitialize_POValues[0]);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(heli_q8_M, _rt_error_message);
        return;
      }
    }
  }

  /* Start for S-Function (hil_read_encoder_timebase_block): '<S4>/HIL Read Encoder Timebase' */

  /* S-Function Block: heli_q8/Heli 3D/HIL Read Encoder Timebase (hil_read_encoder_timebase_block) */
  {
    t_error result;
    result = hil_task_create_encoder_reader(heli_q8_DW.HILInitialize_Card,
      heli_q8_P.HILReadEncoderTimebase_SamplesI,
      heli_q8_P.HILReadEncoderTimebase_Channels, 3,
      &heli_q8_DW.HILReadEncoderTimebase_Task);
    if (result >= 0) {
      result = hil_task_set_buffer_overflow_mode
        (heli_q8_DW.HILReadEncoderTimebase_Task, (t_buffer_overflow_mode)
         (heli_q8_P.HILReadEncoderTimebase_Overflow - 1));
    }

    if (result < 0) {
      msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
        (_rt_error_message));
      rtmSetErrorStatus(heli_q8_M, _rt_error_message);
    }
  }

  /* Start for S-Function (stream_call_block): '<S5>/Stream Call1' incorporates:
   *  Constant: '<S5>/Constant'
   *  S-Function (string_constant_block): '<S5>/String Constant'
   */

  /* S-Function Block: heli_q8/IMU1/Stream Call1 (stream_call_block) */
  {
    heli_q8_DW.StreamCall1_State = STREAM_CALL_STATE_NOT_CONNECTED;
    heli_q8_DW.StreamCall1_Stream = NULL;
  }

  /* Start for RateTransition: '<S6>/Rate Transition: x' */
  heli_q8_B.RateTransitionx = heli_q8_P.RateTransitionx_InitialConditio;

  /* Start for RateTransition: '<S6>/Rate Transition: y' */
  heli_q8_B.RateTransitiony = heli_q8_P.RateTransitiony_InitialConditio;

  /* Start for ToFile: '<Root>/To File' */
  {
    FILE *fp = (NULL);
    char fileName[509] = "tempDataFile.mat";
    if ((fp = fopen(fileName, "wb")) == (NULL)) {
      rtmSetErrorStatus(heli_q8_M, "Error creating .mat file tempDataFile.mat");
      return;
    }

    if (rt_WriteMat4FileHeader(fp, 15 + 1, 0, "data")) {
      rtmSetErrorStatus(heli_q8_M,
                        "Error writing mat file header to file tempDataFile.mat");
      return;
    }

    heli_q8_DW.ToFile_IWORK.Count = 0;
    heli_q8_DW.ToFile_IWORK.Decimation = -1;
    heli_q8_DW.ToFile_PWORK.FilePtr = fp;
  }

  /* Start for S-Function (game_controller_block): '<S6>/Game Controller' */

  /* S-Function Block: heli_q8/Joystick/Game Controller (game_controller_block) */
  {
    if (heli_q8_P.GameController_Enabled) {
      t_double deadzone[6];
      t_double saturation[6];
      t_int index;
      t_error result;
      for (index = 0; index < 6; index++) {
        deadzone[index] = -1;
      }

      for (index = 0; index < 6; index++) {
        saturation[index] = -1;
      }

      result = game_controller_open(heli_q8_P.GameController_ControllerNumber,
        heli_q8_P.GameController_BufferSize, deadzone, saturation,
        heli_q8_P.GameController_AutoCenter, 0, 1.0,
        &heli_q8_DW.GameController_Controller);
      if (result < 0) {
        msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
          (_rt_error_message));
        rtmSetErrorStatus(heli_q8_M, _rt_error_message);
      }
    }
  }

  {
    int_T is;

    /* InitializeConditions for Memory: '<S5>/Memory' */
    memcpy(&heli_q8_DW.Memory_PreviousInput[0],
           &heli_q8_P.Memory_InitialCondition[0], 10U * sizeof(real_T));

    /* InitializeConditions for TransferFcn: '<S4>/Pitch: Transfer Fcn' */
    heli_q8_X.PitchTransferFcn_CSTATE = 0.0;

    /* InitializeConditions for TransferFcn: '<S4>/Elevation: Transfer Fcn' */
    heli_q8_X.ElevationTransferFcn_CSTATE = 0.0;

    /* InitializeConditions for TransferFcn: '<S4>/Travel: Transfer Fcn' */
    heli_q8_X.TravelTransferFcn_CSTATE = 0.0;

    /* InitializeConditions for RateTransition: '<S6>/Rate Transition: x' */
    heli_q8_DW.RateTransitionx_Buffer0 =
      heli_q8_P.RateTransitionx_InitialConditio;

    /* InitializeConditions for RateTransition: '<S6>/Rate Transition: y' */
    heli_q8_DW.RateTransitiony_Buffer0 =
      heli_q8_P.RateTransitiony_InitialConditio;

    /* InitializeConditions for StateSpace: '<S8>/State-Space' */
    for (is = 0; is < 5; is++) {
      heli_q8_X.StateSpace_CSTATE[is] = heli_q8_P.StateSpace_InitialCondition[is];
    }

    /* End of InitializeConditions for StateSpace: '<S8>/State-Space' */

    /* InitializeConditions for Integrator: '<S7>/Integrator1' */
    heli_q8_X.Integrator1_CSTATE = heli_q8_P.Integrator1_IC;

    /* InitializeConditions for Integrator: '<S7>/Integrator' */
    heli_q8_X.Integrator_CSTATE = heli_q8_P.Integrator_IC;

    /* InitializeConditions for Integrator: '<S12>/Integrator' */
    heli_q8_X.Integrator_CSTATE_n = heli_q8_P.Integrator_IC_k;
  }
}

/* Model terminate function */
void heli_q8_terminate(void)
{
  /* Terminate for S-Function (hil_initialize_block): '<Root>/HIL Initialize' */

  /* S-Function Block: heli_q8/HIL Initialize (hil_initialize_block) */
  {
    t_boolean is_switching;
    t_int result;
    t_uint32 num_final_analog_outputs = 0;
    t_uint32 num_final_pwm_outputs = 0;
    hil_task_stop_all(heli_q8_DW.HILInitialize_Card);
    hil_monitor_stop_all(heli_q8_DW.HILInitialize_Card);
    is_switching = false;
    if ((heli_q8_P.HILInitialize_AOTerminate && !is_switching) ||
        (heli_q8_P.HILInitialize_AOExit && is_switching)) {
      {
        int_T i1;
        real_T *dw_AOVoltages = &heli_q8_DW.HILInitialize_AOVoltages[0];
        for (i1=0; i1 < 8; i1++) {
          dw_AOVoltages[i1] = heli_q8_P.HILInitialize_AOFinal;
        }
      }

      num_final_analog_outputs = 8U;
    } else {
      num_final_analog_outputs = 0;
    }

    if ((heli_q8_P.HILInitialize_POTerminate && !is_switching) ||
        (heli_q8_P.HILInitialize_POExit && is_switching)) {
      {
        int_T i1;
        real_T *dw_POValues = &heli_q8_DW.HILInitialize_POValues[0];
        for (i1=0; i1 < 8; i1++) {
          dw_POValues[i1] = heli_q8_P.HILInitialize_POFinal;
        }
      }

      num_final_pwm_outputs = 8U;
    } else {
      num_final_pwm_outputs = 0;
    }

    if (0
        || num_final_analog_outputs > 0
        || num_final_pwm_outputs > 0
        ) {
      /* Attempt to write the final outputs atomically (due to firmware issue in old Q2-USB). Otherwise write channels individually */
      result = hil_write(heli_q8_DW.HILInitialize_Card
                         , heli_q8_P.HILInitialize_AOChannels,
                         num_final_analog_outputs
                         , heli_q8_P.HILInitialize_POChannels,
                         num_final_pwm_outputs
                         , NULL, 0
                         , NULL, 0
                         , &heli_q8_DW.HILInitialize_AOVoltages[0]
                         , &heli_q8_DW.HILInitialize_POValues[0]
                         , (t_boolean *) NULL
                         , NULL
                         );
      if (result == -QERR_HIL_WRITE_NOT_SUPPORTED) {
        t_error local_result;
        result = 0;

        /* The hil_write operation is not supported by this card. Write final outputs for each channel type */
        if (num_final_analog_outputs > 0) {
          local_result = hil_write_analog(heli_q8_DW.HILInitialize_Card,
            heli_q8_P.HILInitialize_AOChannels, num_final_analog_outputs,
            &heli_q8_DW.HILInitialize_AOVoltages[0]);
          if (local_result < 0) {
            result = local_result;
          }
        }

        if (num_final_pwm_outputs > 0) {
          local_result = hil_write_pwm(heli_q8_DW.HILInitialize_Card,
            heli_q8_P.HILInitialize_POChannels, num_final_pwm_outputs,
            &heli_q8_DW.HILInitialize_POValues[0]);
          if (local_result < 0) {
            result = local_result;
          }
        }

        if (result < 0) {
          msg_get_error_messageA(NULL, result, _rt_error_message, sizeof
            (_rt_error_message));
          rtmSetErrorStatus(heli_q8_M, _rt_error_message);
        }
      }
    }

    hil_task_delete_all(heli_q8_DW.HILInitialize_Card);
    hil_monitor_delete_all(heli_q8_DW.HILInitialize_Card);
    hil_close(heli_q8_DW.HILInitialize_Card);
    heli_q8_DW.HILInitialize_Card = NULL;
  }

  /* Terminate for S-Function (stream_call_block): '<S5>/Stream Call1' incorporates:
   *  Constant: '<S5>/Constant'
   *  S-Function (string_constant_block): '<S5>/String Constant'
   */

  /* S-Function Block: heli_q8/IMU1/Stream Call1 (stream_call_block) */
  {
    if (heli_q8_DW.StreamCall1_Stream != NULL) {
      stream_close(heli_q8_DW.StreamCall1_Stream);
      heli_q8_DW.StreamCall1_Stream = NULL;
    }
  }

  /* Terminate for ToFile: '<Root>/To File' */
  {
    FILE *fp = (FILE *) heli_q8_DW.ToFile_PWORK.FilePtr;
    if (fp != (NULL)) {
      char fileName[509] = "tempDataFile.mat";
      if (fclose(fp) == EOF) {
        rtmSetErrorStatus(heli_q8_M, "Error closing MAT-file tempDataFile.mat");
        return;
      }

      if ((fp = fopen(fileName, "r+b")) == (NULL)) {
        rtmSetErrorStatus(heli_q8_M, "Error reopening MAT-file tempDataFile.mat");
        return;
      }

      if (rt_WriteMat4FileHeader(fp, 15 + 1, heli_q8_DW.ToFile_IWORK.Count,
           "data")) {
        rtmSetErrorStatus(heli_q8_M,
                          "Error writing header for data to MAT-file tempDataFile.mat");
      }

      if (fclose(fp) == EOF) {
        rtmSetErrorStatus(heli_q8_M, "Error closing MAT-file tempDataFile.mat");
        return;
      }

      heli_q8_DW.ToFile_PWORK.FilePtr = (NULL);
    }
  }

  /* Terminate for S-Function (game_controller_block): '<S6>/Game Controller' */

  /* S-Function Block: heli_q8/Joystick/Game Controller (game_controller_block) */
  {
    if (heli_q8_P.GameController_Enabled) {
      game_controller_close(heli_q8_DW.GameController_Controller);
      heli_q8_DW.GameController_Controller = NULL;
    }
  }
}

/*========================================================================*
 * Start of Classic call interface                                        *
 *========================================================================*/

/* Solver interface called by GRT_Main */
#ifndef USE_GENERATED_SOLVER

void rt_ODECreateIntegrationData(RTWSolverInfo *si)
{
  UNUSED_PARAMETER(si);
  return;
}                                      /* do nothing */

void rt_ODEDestroyIntegrationData(RTWSolverInfo *si)
{
  UNUSED_PARAMETER(si);
  return;
}                                      /* do nothing */

void rt_ODEUpdateContinuousStates(RTWSolverInfo *si)
{
  UNUSED_PARAMETER(si);
  return;
}                                      /* do nothing */

#endif

void MdlOutputs(int_T tid)
{
  heli_q8_output();
  UNUSED_PARAMETER(tid);
}

void MdlUpdate(int_T tid)
{
  heli_q8_update();
  UNUSED_PARAMETER(tid);
}

void MdlInitializeSizes(void)
{
}

void MdlInitializeSampleTimes(void)
{
}

void MdlInitialize(void)
{
}

void MdlStart(void)
{
  heli_q8_initialize();
}

void MdlTerminate(void)
{
  heli_q8_terminate();
}

/* Registration function */
RT_MODEL_heli_q8_T *heli_q8(void)
{
  /* Registration code */

  /* initialize non-finites */
  rt_InitInfAndNaN(sizeof(real_T));

  /* non-finite (run-time) assignments */
  heli_q8_P.Integrator_UpperSat = rtInf;
  heli_q8_P.Integrator_LowerSat = rtMinusInf;

  /* initialize real-time model */
  (void) memset((void *)heli_q8_M, 0,
                sizeof(RT_MODEL_heli_q8_T));

  {
    /* Setup solver object */
    rtsiSetSimTimeStepPtr(&heli_q8_M->solverInfo, &heli_q8_M->Timing.simTimeStep);
    rtsiSetTPtr(&heli_q8_M->solverInfo, &rtmGetTPtr(heli_q8_M));
    rtsiSetStepSizePtr(&heli_q8_M->solverInfo, &heli_q8_M->Timing.stepSize0);
    rtsiSetdXPtr(&heli_q8_M->solverInfo, &heli_q8_M->derivs);
    rtsiSetContStatesPtr(&heli_q8_M->solverInfo, (real_T **)
                         &heli_q8_M->contStates);
    rtsiSetNumContStatesPtr(&heli_q8_M->solverInfo,
      &heli_q8_M->Sizes.numContStates);
    rtsiSetNumPeriodicContStatesPtr(&heli_q8_M->solverInfo,
      &heli_q8_M->Sizes.numPeriodicContStates);
    rtsiSetPeriodicContStateIndicesPtr(&heli_q8_M->solverInfo,
      &heli_q8_M->periodicContStateIndices);
    rtsiSetPeriodicContStateRangesPtr(&heli_q8_M->solverInfo,
      &heli_q8_M->periodicContStateRanges);
    rtsiSetErrorStatusPtr(&heli_q8_M->solverInfo, (&rtmGetErrorStatus(heli_q8_M)));
    rtsiSetRTModelPtr(&heli_q8_M->solverInfo, heli_q8_M);
  }

  rtsiSetSimTimeStep(&heli_q8_M->solverInfo, MAJOR_TIME_STEP);
  heli_q8_M->intgData.f[0] = heli_q8_M->odeF[0];
  heli_q8_M->contStates = ((real_T *) &heli_q8_X);
  rtsiSetSolverData(&heli_q8_M->solverInfo, (void *)&heli_q8_M->intgData);
  rtsiSetSolverName(&heli_q8_M->solverInfo,"ode1");

  /* Initialize timing info */
  {
    int_T *mdlTsMap = heli_q8_M->Timing.sampleTimeTaskIDArray;
    mdlTsMap[0] = 0;
    mdlTsMap[1] = 1;
    mdlTsMap[2] = 2;
    mdlTsMap[3] = 3;
    heli_q8_M->Timing.sampleTimeTaskIDPtr = (&mdlTsMap[0]);
    heli_q8_M->Timing.sampleTimes = (&heli_q8_M->Timing.sampleTimesArray[0]);
    heli_q8_M->Timing.offsetTimes = (&heli_q8_M->Timing.offsetTimesArray[0]);

    /* task periods */
    heli_q8_M->Timing.sampleTimes[0] = (0.0);
    heli_q8_M->Timing.sampleTimes[1] = (0.002);
    heli_q8_M->Timing.sampleTimes[2] = (0.01);
    heli_q8_M->Timing.sampleTimes[3] = (5.0);

    /* task offsets */
    heli_q8_M->Timing.offsetTimes[0] = (0.0);
    heli_q8_M->Timing.offsetTimes[1] = (0.0);
    heli_q8_M->Timing.offsetTimes[2] = (0.0);
    heli_q8_M->Timing.offsetTimes[3] = (0.0);
  }

  rtmSetTPtr(heli_q8_M, &heli_q8_M->Timing.tArray[0]);

  {
    int_T *mdlSampleHits = heli_q8_M->Timing.sampleHitArray;
    mdlSampleHits[0] = 1;
    mdlSampleHits[1] = 1;
    mdlSampleHits[2] = 1;
    mdlSampleHits[3] = 1;
    heli_q8_M->Timing.sampleHits = (&mdlSampleHits[0]);
  }

  rtmSetTFinal(heli_q8_M, 55.0);
  heli_q8_M->Timing.stepSize0 = 0.002;
  heli_q8_M->Timing.stepSize1 = 0.002;
  heli_q8_M->Timing.stepSize2 = 0.01;
  heli_q8_M->Timing.stepSize3 = 5.0;

  /* External mode info */
  heli_q8_M->Sizes.checksums[0] = (2910462947U);
  heli_q8_M->Sizes.checksums[1] = (2720806051U);
  heli_q8_M->Sizes.checksums[2] = (1706320024U);
  heli_q8_M->Sizes.checksums[3] = (3194207740U);

  {
    static const sysRanDType rtAlwaysEnabled = SUBSYS_RAN_BC_ENABLE;
    static RTWExtModeInfo rt_ExtModeInfo;
    static const sysRanDType *systemRan[4];
    heli_q8_M->extModeInfo = (&rt_ExtModeInfo);
    rteiSetSubSystemActiveVectorAddresses(&rt_ExtModeInfo, systemRan);
    systemRan[0] = &rtAlwaysEnabled;
    systemRan[1] = &rtAlwaysEnabled;
    systemRan[2] = &rtAlwaysEnabled;
    systemRan[3] = &rtAlwaysEnabled;
    rteiSetModelMappingInfoPtr(heli_q8_M->extModeInfo,
      &heli_q8_M->SpecialInfo.mappingInfo);
    rteiSetChecksumsPtr(heli_q8_M->extModeInfo, heli_q8_M->Sizes.checksums);
    rteiSetTPtr(heli_q8_M->extModeInfo, rtmGetTPtr(heli_q8_M));
  }

  heli_q8_M->solverInfoPtr = (&heli_q8_M->solverInfo);
  heli_q8_M->Timing.stepSize = (0.002);
  rtsiSetFixedStepSize(&heli_q8_M->solverInfo, 0.002);
  rtsiSetSolverMode(&heli_q8_M->solverInfo, SOLVER_MODE_SINGLETASKING);

  /* block I/O */
  heli_q8_M->blockIO = ((void *) &heli_q8_B);
  (void) memset(((void *) &heli_q8_B), 0,
                sizeof(B_heli_q8_T));

  {
    int32_T i;
    for (i = 0; i < 10; i++) {
      heli_q8_B.Switch[i] = 0.0;
    }

    for (i = 0; i < 5; i++) {
      heli_q8_B.StateSpace[i] = 0.0;
    }

    for (i = 0; i < 15; i++) {
      heli_q8_B.TmpSignalConversionAtToFileInpo[i] = 0.0;
    }

    for (i = 0; i < 7; i++) {
      heli_q8_B.TmpSignalConversionAtStateSpace[i] = 0.0;
    }

    for (i = 0; i < 5; i++) {
      heli_q8_B.y[i] = 0.0;
    }

    heli_q8_B.Gain2[0] = 0.0;
    heli_q8_B.Gain2[1] = 0.0;
    heli_q8_B.Gain2[2] = 0.0;
    heli_q8_B.Gain1[0] = 0.0;
    heli_q8_B.Gain1[1] = 0.0;
    heli_q8_B.Gain1[2] = 0.0;
    heli_q8_B.Atan = 0.0;
    heli_q8_B.Atan1 = 0.0;
    heli_q8_B.PitchCounttorad = 0.0;
    heli_q8_B.PitchTransferFcn = 0.0;
    heli_q8_B.ElevationCounttorad = 0.0;
    heli_q8_B.ElevationTransferFcn = 0.0;
    heli_q8_B.TravelCounttorad = 0.0;
    heli_q8_B.TravelTransferFcn = 0.0;
    heli_q8_B.RateTransitionx = 0.0;
    heli_q8_B.Joystick_gain_x = 0.0;
    heli_q8_B.RateTransitiony = 0.0;
    heli_q8_B.Joystick_gain_y = 0.0;
    heli_q8_B.Add = 0.0;
    heli_q8_B.Add1 = 0.0;
    heli_q8_B.Gain[0] = 0.0;
    heli_q8_B.Gain[1] = 0.0;
    heli_q8_B.Integrator1 = 0.0;
    heli_q8_B.Sum3 = 0.0;
    heli_q8_B.Sum[0] = 0.0;
    heli_q8_B.Sum[1] = 0.0;
    heli_q8_B.FrontmotorSaturation = 0.0;
    heli_q8_B.BackmotorSaturation = 0.0;
    heli_q8_B.GameController_o4 = 0.0;
    heli_q8_B.GameController_o5 = 0.0;
    heli_q8_B.Sum1 = 0.0;
    heli_q8_B.Sum2 = 0.0;
    heli_q8_B.K_ei = 0.0;
    heli_q8_B.Gain1_o = 0.0;
    heli_q8_B.Gain_b = 0.0;
    heli_q8_B.euler_rates[0] = 0.0;
    heli_q8_B.euler_rates[1] = 0.0;
    heli_q8_B.euler_rates[2] = 0.0;
  }

  /* parameters */
  heli_q8_M->defaultParam = ((real_T *)&heli_q8_P);

  /* states (continuous) */
  {
    real_T *x = (real_T *) &heli_q8_X;
    heli_q8_M->contStates = (x);
    (void) memset((void *)&heli_q8_X, 0,
                  sizeof(X_heli_q8_T));
  }

  /* states (dwork) */
  heli_q8_M->dwork = ((void *) &heli_q8_DW);
  (void) memset((void *)&heli_q8_DW, 0,
                sizeof(DW_heli_q8_T));

  {
    int32_T i;
    for (i = 0; i < 8; i++) {
      heli_q8_DW.HILInitialize_AIMinimums[i] = 0.0;
    }
  }

  {
    int32_T i;
    for (i = 0; i < 8; i++) {
      heli_q8_DW.HILInitialize_AIMaximums[i] = 0.0;
    }
  }

  {
    int32_T i;
    for (i = 0; i < 8; i++) {
      heli_q8_DW.HILInitialize_AOMinimums[i] = 0.0;
    }
  }

  {
    int32_T i;
    for (i = 0; i < 8; i++) {
      heli_q8_DW.HILInitialize_AOMaximums[i] = 0.0;
    }
  }

  {
    int32_T i;
    for (i = 0; i < 8; i++) {
      heli_q8_DW.HILInitialize_AOVoltages[i] = 0.0;
    }
  }

  {
    int32_T i;
    for (i = 0; i < 8; i++) {
      heli_q8_DW.HILInitialize_FilterFrequency[i] = 0.0;
    }
  }

  {
    int32_T i;
    for (i = 0; i < 8; i++) {
      heli_q8_DW.HILInitialize_POSortedFreqs[i] = 0.0;
    }
  }

  {
    int32_T i;
    for (i = 0; i < 8; i++) {
      heli_q8_DW.HILInitialize_POValues[i] = 0.0;
    }
  }

  {
    int32_T i;
    for (i = 0; i < 10; i++) {
      heli_q8_DW.Memory_PreviousInput[i] = 0.0;
    }
  }

  heli_q8_DW.RateTransitionx_Buffer0 = 0.0;
  heli_q8_DW.RateTransitiony_Buffer0 = 0.0;
  heli_q8_DW.HILWriteAnalog_Buffer[0] = 0.0;
  heli_q8_DW.HILWriteAnalog_Buffer[1] = 0.0;

  /* data type transition information */
  {
    static DataTypeTransInfo dtInfo;
    (void) memset((char_T *) &dtInfo, 0,
                  sizeof(dtInfo));
    heli_q8_M->SpecialInfo.mappingInfo = (&dtInfo);
    dtInfo.numDataTypes = 25;
    dtInfo.dataTypeSizes = &rtDataTypeSizes[0];
    dtInfo.dataTypeNames = &rtDataTypeNames[0];

    /* Block I/O transition table */
    dtInfo.BTransTable = &rtBTransTable;

    /* Parameters transition table */
    dtInfo.PTransTable = &rtPTransTable;
  }

  /* Initialize Sizes */
  heli_q8_M->Sizes.numContStates = (11);/* Number of continuous states */
  heli_q8_M->Sizes.numPeriodicContStates = (0);
                                      /* Number of periodic continuous states */
  heli_q8_M->Sizes.numY = (0);         /* Number of model outputs */
  heli_q8_M->Sizes.numU = (0);         /* Number of model inputs */
  heli_q8_M->Sizes.sysDirFeedThru = (0);/* The model is not direct feedthrough */
  heli_q8_M->Sizes.numSampTimes = (4); /* Number of sample times */
  heli_q8_M->Sizes.numBlocks = (110);  /* Number of blocks */
  heli_q8_M->Sizes.numBlockIO = (37);  /* Number of block outputs */
  heli_q8_M->Sizes.numBlockPrms = (544);/* Sum of parameter "widths" */
  return heli_q8_M;
}

/*========================================================================*
 * End of Classic call interface                                          *
 *========================================================================*/
