#ifndef __RECEIVE_HPP__
#define __RECEIVE_HPP__

#include "hlsmac.hpp"
#include "ap_int.h"
#include <hls_stream.h>

typedef struct{
    ap_uint<8>      rxd;
    ap_uint<1>      dv;
    ap_uint<1>      er;
}t_s_gmii;

typedef struct {
	ap_uint<14>     count;
	ap_uint<1>      good;
	ap_uint<1>      broad;
	ap_uint<1>      multi;
	ap_uint<1>      under;
	ap_uint<1>      len_err;
	ap_uint<1>      fcs_err;
	ap_uint<1>      data_err;
	ap_uint<1>      ext_err;
	ap_uint<1>      over;
}t_rx_status;

void receive(hls::stream<t_s_gmii> &s_gmii, hls::stream<t_axis> &m_axis, t_rx_status* rx_status);

#endif
