/*
 * heli_q8_dt.h
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

#include "ext_types.h"

/* data type size table */
static uint_T rtDataTypeSizes[] = {
  sizeof(real_T),
  sizeof(real32_T),
  sizeof(int8_T),
  sizeof(uint8_T),
  sizeof(int16_T),
  sizeof(uint16_T),
  sizeof(int32_T),
  sizeof(uint32_T),
  sizeof(boolean_T),
  sizeof(fcn_call_T),
  sizeof(int_T),
  sizeof(pointer_T),
  sizeof(action_T),
  2*sizeof(uint32_T),
  sizeof(t_stream),
  sizeof(t_stream_ptr),
  sizeof(intmax_t),
  sizeof(ptrdiff_t),
  sizeof(size_t),
  sizeof(t_int64),
  sizeof(t_uint64),
  sizeof(t_wide_char),
  sizeof(t_game_controller),
  sizeof(t_card),
  sizeof(t_task)
};

/* data type name table */
static const char_T * rtDataTypeNames[] = {
  "real_T",
  "real32_T",
  "int8_T",
  "uint8_T",
  "int16_T",
  "uint16_T",
  "int32_T",
  "uint32_T",
  "boolean_T",
  "fcn_call_T",
  "int_T",
  "pointer_T",
  "action_T",
  "timer_uint32_pair_T",
  "t_stream",
  "t_stream_ptr",
  "intmax_t",
  "ptrdiff_t",
  "size_t",
  "t_int64",
  "t_uint64",
  "t_wide_char",
  "t_game_controller",
  "t_card",
  "t_task"
};

/* data type transitions for block I/O structure */
static DataTypeTransition rtBTransitions[] = {
  { (char_T *)(&heli_q8_B.Switch[0]), 0, 0, 80 },

  { (char_T *)(&heli_q8_B.StreamCall1_o2), 3, 0, 1 },

  { (char_T *)(&heli_q8_B.StreamRead1_o3), 8, 0, 1 }
  ,

  { (char_T *)(&heli_q8_DW.HILInitialize_AIMinimums[0]), 0, 0, 78 },

  { (char_T *)(&heli_q8_DW.StreamCall1_Stream), 14, 0, 1 },

  { (char_T *)(&heli_q8_DW.GameController_Controller), 22, 0, 1 },

  { (char_T *)(&heli_q8_DW.HILInitialize_Card), 23, 0, 1 },

  { (char_T *)(&heli_q8_DW.HILReadEncoderTimebase_Task), 24, 0, 1 },

  { (char_T *)(&heli_q8_DW.Acceleration_PWORK.LoggedData), 11, 0, 32 },

  { (char_T *)(&heli_q8_DW.HILInitialize_ClockModes[0]), 6, 0, 46 },

  { (char_T *)(&heli_q8_DW.HILInitialize_POSortedChans[0]), 7, 0, 8 },

  { (char_T *)(&heli_q8_DW.ToFile_IWORK.Count), 10, 0, 1 },

  { (char_T *)(&heli_q8_DW.StreamCall1_State), 3, 0, 1 }
};

/* data type transition table for block I/O structure */
static DataTypeTransitionTable rtBTransTable = {
  13U,
  rtBTransitions
};

/* data type transitions for Parameters structure */
static DataTypeTransition rtPTransitions[] = {
  { (char_T *)(&heli_q8_P.A_est[0]), 0, 0, 104 },

  { (char_T *)(&heli_q8_P.HILWriteAnalog_channels[0]), 7, 0, 2 },

  { (char_T *)(&heli_q8_P.HILInitialize_OOTerminate), 0, 0, 87 },

  { (char_T *)(&heli_q8_P.HILInitialize_CKChannels[0]), 6, 0, 12 },

  { (char_T *)(&heli_q8_P.HILInitialize_AIChannels[0]), 7, 0, 38 },

  { (char_T *)(&heli_q8_P.GameController_BufferSize), 5, 0, 1 },

  { (char_T *)(&heli_q8_P.HILInitialize_Active), 8, 0, 41 },

  { (char_T *)(&heli_q8_P.HILReadEncoderTimebase_Overflow), 3, 0, 259 }
};

/* data type transition table for Parameters structure */
static DataTypeTransitionTable rtPTransTable = {
  8U,
  rtPTransitions
};

/* [EOF] heli_q8_dt.h */
