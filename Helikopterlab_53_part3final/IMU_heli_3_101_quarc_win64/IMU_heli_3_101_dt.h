/*
 * IMU_heli_3_101_dt.h
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
  sizeof(t_wide_char)
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
  "t_wide_char"
};

/* data type transitions for block I/O structure */
static DataTypeTransition rtBTransitions[] = {
  { (char_T *)(&IMU_heli_3_101_B.Switch[0]), 0, 0, 21 },

  { (char_T *)(&IMU_heli_3_101_B.StreamCall1_o2), 3, 0, 1 }
  ,

  { (char_T *)(&IMU_heli_3_101_DW.Memory_PreviousInput[0]), 0, 0, 10 },

  { (char_T *)(&IMU_heli_3_101_DW.StreamCall1_Stream), 14, 0, 1 },

  { (char_T *)(&IMU_heli_3_101_DW.Acceleration_PWORK.LoggedData), 11, 0, 5 },

  { (char_T *)(&IMU_heli_3_101_DW.StreamCall1_State), 3, 0, 1 }
};

/* data type transition table for block I/O structure */
static DataTypeTransitionTable rtBTransTable = {
  6U,
  rtBTransitions
};

/* data type transitions for Parameters structure */
static DataTypeTransition rtPTransitions[] = {
  { (char_T *)(&IMU_heli_3_101_P.Constant_Value), 0, 0, 30 },

  { (char_T *)(&IMU_heli_3_101_P.StreamCall1_SendBufferSize), 6, 0, 2 },

  { (char_T *)(&IMU_heli_3_101_P.StreamFormattedWrite_MaxUnits), 7, 0, 1 },

  { (char_T *)(&IMU_heli_3_101_P.StreamCall1_NonBlocking), 8, 0, 2 },

  { (char_T *)(&IMU_heli_3_101_P.StringConstant_Value[0]), 3, 0, 257 }
};

/* data type transition table for Parameters structure */
static DataTypeTransitionTable rtPTransTable = {
  5U,
  rtPTransitions
};

/* [EOF] IMU_heli_3_101_dt.h */
