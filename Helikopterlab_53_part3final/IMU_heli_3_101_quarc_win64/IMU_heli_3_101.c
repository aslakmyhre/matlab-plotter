/*
 * IMU_heli_3_101.c
 *
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * Code generation for model "IMU_heli_3_101".
 *
 * Model version              : 11.2
 * Simulink Coder version : 9.4 (R2020b) 29-Jul-2020
 * C source code generated on : Thu Oct 22 15:08:53 2026
 *
 * Target selection: quarc_win64.tlc
 * Note: GRT includes extra infrastructure and instrumentation for prototyping
 * Embedded hardware selection: Intel->x86-64 (Windows64)
 * Code generation objectives: Unspecified
 * Validation result: Not run
 */

#include "IMU_heli_3_101.h"
#include "IMU_heli_3_101_private.h"
#include "IMU_heli_3_101_dt.h"

t_stream IMU_heli_3_101_rtZt_stream = NULL;

/* Block signals (default storage) */
B_IMU_heli_3_101_T IMU_heli_3_101_B;

/* Block states (default storage) */
DW_IMU_heli_3_101_T IMU_heli_3_101_DW;

/* Real-time model */
static RT_MODEL_IMU_heli_3_101_T IMU_heli_3_101_M_;
RT_MODEL_IMU_heli_3_101_T *const IMU_heli_3_101_M = &IMU_heli_3_101_M_;

/* Model output function */
void IMU_heli_3_101_output(void)
{
  /* local block i/o variables */
  t_stream_ptr rtb_StreamCall1_o1;
  real32_T rtb_StreamRead1_o2[10];
  int32_T rtb_StreamFormattedWrite_o2;
  int32_T rtb_StreamCall1_o3;
  boolean_T rtb_StreamRead1_o3;
  real_T tmp[9];
  real_T euler_rates_tmp;
  real_T euler_rates_tmp_0;
  real_T euler_rates_tmp_1;
  real_T euler_rates_tmp_2;
  int32_T i;

  /* S-Function (stream_call_block): '<S2>/Stream Call1' incorporates:
   *  Constant: '<S2>/Constant'
   *  S-Function (string_constant_block): '<S2>/String Constant'
   */

  /* S-Function Block: IMU_heli_3_101/IMU/Stream Call1 (stream_call_block) */
  {
    t_error result = 0;
    t_boolean close_flag = (IMU_heli_3_101_P.Constant_Value != 0);
    rtb_StreamCall1_o1 = NULL;
    switch (IMU_heli_3_101_DW.StreamCall1_State) {
     case STREAM_CALL_STATE_NOT_CONNECTED:
      {
        if (!close_flag) {
          /* Make sure URI is null-terminated */
          if (string_length((char *) IMU_heli_3_101_P.StringConstant_Value, 255)
              == 255) {
            rtmSetErrorStatus(IMU_heli_3_101_M,
                              "URI passed to Stream Call block is not null-terminated!");
            result = -QERR_STRING_NOT_TERMINATED;
          } else {
            result = stream_connect((char *)
              IMU_heli_3_101_P.StringConstant_Value,
              IMU_heli_3_101_P.StreamCall1_NonBlocking != 0,
              IMU_heli_3_101_P.StreamCall1_SendBufferSize,
              IMU_heli_3_101_P.StreamCall1_ReceiveBufferSize,
              &IMU_heli_3_101_DW.StreamCall1_Stream);
            if (result == 0) {
              IMU_heli_3_101_DW.StreamCall1_State = STREAM_CALL_STATE_CONNECTED;
              stream_set_byte_order(IMU_heli_3_101_DW.StreamCall1_Stream,
                                    (t_stream_byte_order)
                                    IMU_heli_3_101_P.StreamCall1_Endian);
              rtb_StreamCall1_o1 = &IMU_heli_3_101_DW.StreamCall1_Stream;
            } else if (result == -QERR_WOULD_BLOCK) {
              IMU_heli_3_101_DW.StreamCall1_State = STREAM_CALL_STATE_CONNECTING;
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

          result = stream_poll(IMU_heli_3_101_DW.StreamCall1_Stream, &timeout,
                               STREAM_POLL_CONNECT);
          if (result > 0) {
            IMU_heli_3_101_DW.StreamCall1_State = STREAM_CALL_STATE_CONNECTED;
            stream_set_byte_order(IMU_heli_3_101_DW.StreamCall1_Stream,
                                  (t_stream_byte_order)
                                  IMU_heli_3_101_P.StreamCall1_Endian);
            rtb_StreamCall1_o1 = &IMU_heli_3_101_DW.StreamCall1_Stream;
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
        rtb_StreamCall1_o1 = &IMU_heli_3_101_DW.StreamCall1_Stream;
        if (!close_flag) {
          break;
        }

        /* Fall through deliberately */
      }

     default:
      {
        t_error close_result = stream_close(IMU_heli_3_101_DW.StreamCall1_Stream);
        if (close_result == 0) {
          IMU_heli_3_101_DW.StreamCall1_State = STREAM_CALL_STATE_NOT_CONNECTED;
          IMU_heli_3_101_DW.StreamCall1_Stream = NULL;
          rtb_StreamCall1_o1 = NULL;
        } else if (result == 0) {
          result = close_result;
        }
        break;
      }
    }

    IMU_heli_3_101_B.StreamCall1_o2 = IMU_heli_3_101_DW.StreamCall1_State;
    rtb_StreamCall1_o3 = (int32_T) result;
  }

  /* S-Function (stream_formatted_write_block): '<S2>/Stream Formatted Write' incorporates:
   *  Constant: '<S2>/Constant1'
   */
  {
    t_error result;
    if (rtb_StreamCall1_o1 != NULL) {
      result = stream_print_utf8_char_array(*rtb_StreamCall1_o1,
        IMU_heli_3_101_P.StreamFormattedWrite_MaxUnits,
        &rtb_StreamFormattedWrite_o2, "%c\n"
        , (char) IMU_heli_3_101_P.Constant1_Value
        );
      if (result > 0) {
        result = stream_flush(*rtb_StreamCall1_o1);
      }

      if (result == -QERR_WOULD_BLOCK) {
        result = 0;
      }
    }
  }

  /* S-Function (stream_read_block): '<S2>/Stream Read1' incorporates:
   *  Constant: '<S2>/Constant1'
   *  S-Function (stream_call_block): '<S2>/Stream Call1'
   *  S-Function (stream_formatted_write_block): '<S2>/Stream Formatted Write'
   */

  /* S-Function Block: IMU_heli_3_101/IMU/Stream Read1 (stream_read_block) */
  {
    t_error result;
    memset(&rtb_StreamRead1_o2[0], 0, 10 * sizeof(real32_T));
    if (((t_stream_ptr)rtb_StreamCall1_o1) != NULL) {
      result = stream_receive_unit_array(*((t_stream_ptr)rtb_StreamCall1_o1),
        &rtb_StreamRead1_o2[0], sizeof(real32_T), 10);
      rtb_StreamRead1_o3 = (result > 0);
      if (result > 0 || result == -QERR_WOULD_BLOCK) {
        result = 0;
      }
    } else {
      rtb_StreamRead1_o3 = false;
      result = 0;
    }
  }

  for (i = 0; i < 10; i++) {
    /* Switch: '<S2>/Switch' */
    if (rtb_StreamRead1_o3) {
      /* Switch: '<S2>/Switch' incorporates:
       *  DataTypeConversion: '<S2>/Data Type Conversion'
       */
      IMU_heli_3_101_B.Switch[i] = rtb_StreamRead1_o2[i];
    } else {
      /* Switch: '<S2>/Switch' incorporates:
       *  Memory: '<S2>/Memory'
       */
      IMU_heli_3_101_B.Switch[i] = IMU_heli_3_101_DW.Memory_PreviousInput[i];
    }

    /* End of Switch: '<S2>/Switch' */
  }

  for (i = 0; i < 3; i++) {
    /* Gain: '<S2>/Gain2' */
    IMU_heli_3_101_B.Gain2[i] = 0.0;
    IMU_heli_3_101_B.Gain2[i] += IMU_heli_3_101_P.Gain2_Gain[i] *
      IMU_heli_3_101_B.Switch[0];
    IMU_heli_3_101_B.Gain2[i] += IMU_heli_3_101_P.Gain2_Gain[i + 3] *
      IMU_heli_3_101_B.Switch[1];
    IMU_heli_3_101_B.Gain2[i] += IMU_heli_3_101_P.Gain2_Gain[i + 6] *
      IMU_heli_3_101_B.Switch[2];
  }

  for (i = 0; i < 3; i++) {
    /* Gain: '<S2>/Gain1' */
    IMU_heli_3_101_B.Gain1[i] = 0.0;
    IMU_heli_3_101_B.Gain1[i] += IMU_heli_3_101_P.Gain1_Gain[i] *
      IMU_heli_3_101_B.Switch[3];
    IMU_heli_3_101_B.Gain1[i] += IMU_heli_3_101_P.Gain1_Gain[i + 3] *
      IMU_heli_3_101_B.Switch[4];
    IMU_heli_3_101_B.Gain1[i] += IMU_heli_3_101_P.Gain1_Gain[i + 6] *
      IMU_heli_3_101_B.Switch[5];
  }

  /* Trigonometry: '<Root>/Atan' incorporates:
   *  Product: '<Root>/Divide'
   */
  IMU_heli_3_101_B.Atan = atan(IMU_heli_3_101_B.Gain2[1] /
    IMU_heli_3_101_B.Gain2[2]);

  /* Trigonometry: '<Root>/Atan1' incorporates:
   *  Math: '<Root>/Square'
   *  Math: '<Root>/Square1'
   *  Product: '<Root>/Divide1'
   *  Sqrt: '<Root>/Square Root'
   *  Sum: '<Root>/Sum'
   */
  IMU_heli_3_101_B.Atan1 = atan(IMU_heli_3_101_B.Gain2[0] / sqrt
    (IMU_heli_3_101_B.Gain2[1] * IMU_heli_3_101_B.Gain2[1] +
     IMU_heli_3_101_B.Gain2[2] * IMU_heli_3_101_B.Gain2[2]));

  /* MATLAB Function: '<Root>/Gyro vector to [pitch rate, elevation rate, travle rate]' incorporates:
   *  SignalConversion generated from: '<S1>/ SFunction '
   */
  /* MATLAB Function 'Gyro vector to [pitch rate, elevation rate, travle rate]': '<S1>:1' */
  /* '<S1>:1:3' */
  /* '<S1>:1:4' */
  /* '<S1>:1:8' */
  /* '<S1>:1:11' */
  euler_rates_tmp = tan(IMU_heli_3_101_B.Atan1);
  euler_rates_tmp_0 = sin(IMU_heli_3_101_B.Atan);
  euler_rates_tmp_1 = cos(IMU_heli_3_101_B.Atan);
  euler_rates_tmp_2 = cos(IMU_heli_3_101_B.Atan1);
  tmp[0] = 1.0;
  tmp[3] = euler_rates_tmp_0 * euler_rates_tmp;
  tmp[6] = euler_rates_tmp_1 * euler_rates_tmp;
  tmp[1] = 0.0;
  tmp[4] = euler_rates_tmp_1;
  tmp[7] = -euler_rates_tmp_0;
  tmp[2] = 0.0;
  tmp[5] = euler_rates_tmp_0 / euler_rates_tmp_2;
  tmp[8] = euler_rates_tmp_1 / euler_rates_tmp_2;
  for (i = 0; i < 3; i++) {
    IMU_heli_3_101_B.euler_rates[i] = 0.0;
    IMU_heli_3_101_B.euler_rates[i] += tmp[i] * IMU_heli_3_101_B.Gain1[0];
    IMU_heli_3_101_B.euler_rates[i] += tmp[i + 3] * IMU_heli_3_101_B.Gain1[1];
    IMU_heli_3_101_B.euler_rates[i] += tmp[i + 6] * IMU_heli_3_101_B.Gain1[2];
  }

  /* End of MATLAB Function: '<Root>/Gyro vector to [pitch rate, elevation rate, travle rate]' */
  /* S-Function (stop_with_error_block): '<S2>/Stop with Call Error' */

  /* S-Function Block: IMU_heli_3_101/IMU/Stop with Call Error (stop_with_error_block) */
  {
    if (rtb_StreamCall1_o3 < 0) {
      msg_get_error_messageA(NULL, rtb_StreamCall1_o3, _rt_error_message, sizeof
        (_rt_error_message));
      rtmSetErrorStatus(IMU_heli_3_101_M, _rt_error_message);
      return;
    }
  }
}

/* Model update function */
void IMU_heli_3_101_update(void)
{
  /* Update for Memory: '<S2>/Memory' */
  memcpy(&IMU_heli_3_101_DW.Memory_PreviousInput[0], &IMU_heli_3_101_B.Switch[0],
         10U * sizeof(real_T));

  /* Update absolute time for base rate */
  /* The "clockTick0" counts the number of times the code of this task has
   * been executed. The absolute time is the multiplication of "clockTick0"
   * and "Timing.stepSize0". Size of "clockTick0" ensures timer will not
   * overflow during the application lifespan selected.
   * Timer of this task consists of two 32 bit unsigned integers.
   * The two integers represent the low bits Timing.clockTick0 and the high bits
   * Timing.clockTickH0. When the low bit overflows to 0, the high bits increment.
   */
  if (!(++IMU_heli_3_101_M->Timing.clockTick0)) {
    ++IMU_heli_3_101_M->Timing.clockTickH0;
  }

  IMU_heli_3_101_M->Timing.t[0] = IMU_heli_3_101_M->Timing.clockTick0 *
    IMU_heli_3_101_M->Timing.stepSize0 + IMU_heli_3_101_M->Timing.clockTickH0 *
    IMU_heli_3_101_M->Timing.stepSize0 * 4294967296.0;
}

/* Model initialize function */
void IMU_heli_3_101_initialize(void)
{
  /* Start for S-Function (stream_call_block): '<S2>/Stream Call1' incorporates:
   *  Constant: '<S2>/Constant'
   *  S-Function (string_constant_block): '<S2>/String Constant'
   */

  /* S-Function Block: IMU_heli_3_101/IMU/Stream Call1 (stream_call_block) */
  {
    IMU_heli_3_101_DW.StreamCall1_State = STREAM_CALL_STATE_NOT_CONNECTED;
    IMU_heli_3_101_DW.StreamCall1_Stream = NULL;
  }

  /* InitializeConditions for Memory: '<S2>/Memory' */
  memcpy(&IMU_heli_3_101_DW.Memory_PreviousInput[0],
         &IMU_heli_3_101_P.Memory_InitialCondition[0], 10U * sizeof(real_T));
}

/* Model terminate function */
void IMU_heli_3_101_terminate(void)
{
  /* Terminate for S-Function (stream_call_block): '<S2>/Stream Call1' incorporates:
   *  Constant: '<S2>/Constant'
   *  S-Function (string_constant_block): '<S2>/String Constant'
   */

  /* S-Function Block: IMU_heli_3_101/IMU/Stream Call1 (stream_call_block) */
  {
    if (IMU_heli_3_101_DW.StreamCall1_Stream != NULL) {
      stream_close(IMU_heli_3_101_DW.StreamCall1_Stream);
      IMU_heli_3_101_DW.StreamCall1_Stream = NULL;
    }
  }
}

/*========================================================================*
 * Start of Classic call interface                                        *
 *========================================================================*/
void MdlOutputs(int_T tid)
{
  IMU_heli_3_101_output();
  UNUSED_PARAMETER(tid);
}

void MdlUpdate(int_T tid)
{
  IMU_heli_3_101_update();
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
  IMU_heli_3_101_initialize();
}

void MdlTerminate(void)
{
  IMU_heli_3_101_terminate();
}

/* Registration function */
RT_MODEL_IMU_heli_3_101_T *IMU_heli_3_101(void)
{
  /* Registration code */

  /* initialize non-finites */
  rt_InitInfAndNaN(sizeof(real_T));

  /* initialize real-time model */
  (void) memset((void *)IMU_heli_3_101_M, 0,
                sizeof(RT_MODEL_IMU_heli_3_101_T));

  /* Initialize timing info */
  {
    int_T *mdlTsMap = IMU_heli_3_101_M->Timing.sampleTimeTaskIDArray;
    mdlTsMap[0] = 0;
    IMU_heli_3_101_M->Timing.sampleTimeTaskIDPtr = (&mdlTsMap[0]);
    IMU_heli_3_101_M->Timing.sampleTimes =
      (&IMU_heli_3_101_M->Timing.sampleTimesArray[0]);
    IMU_heli_3_101_M->Timing.offsetTimes =
      (&IMU_heli_3_101_M->Timing.offsetTimesArray[0]);

    /* task periods */
    IMU_heli_3_101_M->Timing.sampleTimes[0] = (0.002);

    /* task offsets */
    IMU_heli_3_101_M->Timing.offsetTimes[0] = (0.0);
  }

  rtmSetTPtr(IMU_heli_3_101_M, &IMU_heli_3_101_M->Timing.tArray[0]);

  {
    int_T *mdlSampleHits = IMU_heli_3_101_M->Timing.sampleHitArray;
    mdlSampleHits[0] = 1;
    IMU_heli_3_101_M->Timing.sampleHits = (&mdlSampleHits[0]);
  }

  rtmSetTFinal(IMU_heli_3_101_M, -1);
  IMU_heli_3_101_M->Timing.stepSize0 = 0.002;

  /* External mode info */
  IMU_heli_3_101_M->Sizes.checksums[0] = (2654818396U);
  IMU_heli_3_101_M->Sizes.checksums[1] = (3025469678U);
  IMU_heli_3_101_M->Sizes.checksums[2] = (4077450295U);
  IMU_heli_3_101_M->Sizes.checksums[3] = (2669967416U);

  {
    static const sysRanDType rtAlwaysEnabled = SUBSYS_RAN_BC_ENABLE;
    static RTWExtModeInfo rt_ExtModeInfo;
    static const sysRanDType *systemRan[3];
    IMU_heli_3_101_M->extModeInfo = (&rt_ExtModeInfo);
    rteiSetSubSystemActiveVectorAddresses(&rt_ExtModeInfo, systemRan);
    systemRan[0] = &rtAlwaysEnabled;
    systemRan[1] = &rtAlwaysEnabled;
    systemRan[2] = &rtAlwaysEnabled;
    rteiSetModelMappingInfoPtr(IMU_heli_3_101_M->extModeInfo,
      &IMU_heli_3_101_M->SpecialInfo.mappingInfo);
    rteiSetChecksumsPtr(IMU_heli_3_101_M->extModeInfo,
                        IMU_heli_3_101_M->Sizes.checksums);
    rteiSetTPtr(IMU_heli_3_101_M->extModeInfo, rtmGetTPtr(IMU_heli_3_101_M));
  }

  IMU_heli_3_101_M->solverInfoPtr = (&IMU_heli_3_101_M->solverInfo);
  IMU_heli_3_101_M->Timing.stepSize = (0.002);
  rtsiSetFixedStepSize(&IMU_heli_3_101_M->solverInfo, 0.002);
  rtsiSetSolverMode(&IMU_heli_3_101_M->solverInfo, SOLVER_MODE_SINGLETASKING);

  /* block I/O */
  IMU_heli_3_101_M->blockIO = ((void *) &IMU_heli_3_101_B);
  (void) memset(((void *) &IMU_heli_3_101_B), 0,
                sizeof(B_IMU_heli_3_101_T));

  /* parameters */
  IMU_heli_3_101_M->defaultParam = ((real_T *)&IMU_heli_3_101_P);

  /* states (dwork) */
  IMU_heli_3_101_M->dwork = ((void *) &IMU_heli_3_101_DW);
  (void) memset((void *)&IMU_heli_3_101_DW, 0,
                sizeof(DW_IMU_heli_3_101_T));

  /* data type transition information */
  {
    static DataTypeTransInfo dtInfo;
    (void) memset((char_T *) &dtInfo, 0,
                  sizeof(dtInfo));
    IMU_heli_3_101_M->SpecialInfo.mappingInfo = (&dtInfo);
    dtInfo.numDataTypes = 22;
    dtInfo.dataTypeSizes = &rtDataTypeSizes[0];
    dtInfo.dataTypeNames = &rtDataTypeNames[0];

    /* Block I/O transition table */
    dtInfo.BTransTable = &rtBTransTable;

    /* Parameters transition table */
    dtInfo.PTransTable = &rtPTransTable;
  }

  /* Initialize Sizes */
  IMU_heli_3_101_M->Sizes.numContStates = (0);/* Number of continuous states */
  IMU_heli_3_101_M->Sizes.numY = (0);  /* Number of model outputs */
  IMU_heli_3_101_M->Sizes.numU = (0);  /* Number of model inputs */
  IMU_heli_3_101_M->Sizes.sysDirFeedThru = (0);/* The model is not direct feedthrough */
  IMU_heli_3_101_M->Sizes.numSampTimes = (1);/* Number of sample times */
  IMU_heli_3_101_M->Sizes.numBlocks = (29);/* Number of blocks */
  IMU_heli_3_101_M->Sizes.numBlockIO = (7);/* Number of block outputs */
  IMU_heli_3_101_M->Sizes.numBlockPrms = (292);/* Sum of parameter "widths" */
  return IMU_heli_3_101_M;
}

/*========================================================================*
 * End of Classic call interface                                          *
 *========================================================================*/
