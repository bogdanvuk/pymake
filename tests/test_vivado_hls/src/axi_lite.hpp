#ifndef __AXI_LITE_HPP__
#define __AXI_LITE_HPP__

#include "ap_int.h"
#include <hls_stream.h>
#include "transmit.hpp"
#include "receive.hpp"

void axi_lite(
              hls::stream<t_tx_status> &tx_status,
			  hls::stream<t_rx_status> &rx_status
             );

#endif
