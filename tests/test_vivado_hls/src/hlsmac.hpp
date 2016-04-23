#ifndef __HLSMAC_HPP__
#define __HLSMAC_HPP__

#include "ap_int.h"
#include <hls_stream.h>

typedef struct{
	ap_uint<8> data;
	ap_uint<1> user;
	ap_uint<1> last;
}t_axis;

#endif
