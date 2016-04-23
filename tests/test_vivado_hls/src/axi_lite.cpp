#include "axi_lite.hpp"

ap_uint<32> reg_rx_bytes = 0;
ap_uint<32> reg_rx_64 = 0;
ap_uint<32> reg_rx_65_127 = 0;
ap_uint<32> reg_rx_128_255 = 0;
ap_uint<32> reg_rx_256_511 = 0;
ap_uint<32> reg_rx_512_1023 = 0;
ap_uint<32> reg_rx_1024_max = 0;
ap_uint<32> reg_tx_64 = 0;
ap_uint<32> reg_tx_65_127 = 0;
ap_uint<32> reg_tx_128_255 = 0;
ap_uint<32> reg_tx_256_511 = 0;
ap_uint<32> reg_tx_512_1023 = 0;
ap_uint<32> reg_tx_1024_max = 0;
ap_uint<32> reg_rx_good = 0;

ap_uint<32> dummy_last = 0;

void axi_lite(
              hls::stream<t_tx_status> &tx_status,
              hls::stream<t_rx_status> &rx_status,
              ap_uint<32>* rx_bytes,
			  ap_uint<32>* rx_64,
              ap_uint<32>* rx_65_127,
              ap_uint<32>* rx_128_255,
              ap_uint<32>* rx_256_511,
              ap_uint<32>* rx_512_1023,
              ap_uint<32>* rx_1024_max,
			  ap_uint<32>* tx_64,
              ap_uint<32>* tx_65_127,
              ap_uint<32>* tx_128_255,
              ap_uint<32>* tx_256_511,
              ap_uint<32>* tx_512_1023,
              ap_uint<32>* tx_1024_max,
              ap_uint<32>* rx_good
              )
{
    //#pragma HLS INTERFACE ap_hs port=tx_status
#pragma HLS data_pack variable=tx_status
#pragma HLS data_pack variable=rx_status

#pragma HLS interface ap_ctrl_none port=return
    //#pragma HLS INTERFACE s_axilite port=return bundle=axi_lite_bus

#pragma HLS INTERFACE ap_none port=rx_bytes
#pragma HLS INTERFACE ap_none port=rx_64
#pragma HLS INTERFACE ap_none port=rx_65_127
#pragma HLS INTERFACE ap_none port=rx_128_255
#pragma HLS INTERFACE ap_none port=rx_256_511
#pragma HLS INTERFACE ap_none port=rx_512_1023
#pragma HLS INTERFACE ap_none port=rx_1024_max
#pragma HLS INTERFACE ap_none port=tx_64
#pragma HLS INTERFACE ap_none port=tx_65_127
#pragma HLS INTERFACE ap_none port=tx_128_255
#pragma HLS INTERFACE ap_none port=tx_256_511
#pragma HLS INTERFACE ap_none port=tx_512_1023
#pragma HLS INTERFACE ap_none port=tx_1024_max
#pragma HLS INTERFACE ap_none port=rx_good

#pragma HLS INTERFACE s_axilite port=rx_bytes bundle=axi_lite_bus offset=0x200
#pragma HLS INTERFACE s_axilite port=rx_64 bundle=axi_lite_bus offset=0x220
#pragma HLS INTERFACE s_axilite port=rx_65_127 bundle=axi_lite_bus offset=0x228
#pragma HLS INTERFACE s_axilite port=rx_128_255 bundle=axi_lite_bus offset=0x230
#pragma HLS INTERFACE s_axilite port=rx_256_511 bundle=axi_lite_bus offset=0x238
#pragma HLS INTERFACE s_axilite port=rx_512_1023 bundle=axi_lite_bus offset=0x240
#pragma HLS INTERFACE s_axilite port=rx_1024_max bundle=axi_lite_bus  offset=0x248
#pragma HLS INTERFACE s_axilite port=tx_64 bundle=axi_lite_bus offset=0x258
#pragma HLS INTERFACE s_axilite port=tx_65_127 bundle=axi_lite_bus offset=0x260
#pragma HLS INTERFACE s_axilite port=tx_128_255 bundle=axi_lite_bus offset=0x268
#pragma HLS INTERFACE s_axilite port=tx_256_511 bundle=axi_lite_bus offset=0x270
#pragma HLS INTERFACE s_axilite port=tx_512_1023 bundle=axi_lite_bus offset=0x278
#pragma HLS INTERFACE s_axilite port=tx_1024_max bundle=axi_lite_bus  offset=0x280
#pragma HLS INTERFACE s_axilite port=rx_good bundle=axi_lite_bus offset=0x290

#pragma HLS INTERFACE s_axilite port=dummy_last bundle=axi_lite_bus  offset=0x4f0

	t_tx_status tx_din;
    int tx_stat_avail = 0;
	t_rx_status rx_din;
    int rx_stat_avail = 0;

    MAIN: while (1) {
        //#pragma HLS PIPELINE rewind

        *rx_bytes = reg_rx_bytes;
        *rx_64 = reg_rx_64;
        *rx_65_127 = reg_rx_65_127;
        *rx_128_255 = reg_rx_128_255;
        *rx_256_511 = reg_rx_256_511;
        *rx_512_1023 = reg_rx_512_1023;
        *rx_1024_max = reg_rx_1024_max;
        *tx_64 = reg_tx_64;
        *tx_65_127 = reg_tx_65_127;
        *tx_128_255 = reg_tx_128_255;
        *tx_256_511 = reg_tx_256_511;
        *tx_512_1023 = reg_tx_512_1023;
        *tx_1024_max = reg_tx_1024_max;
        *rx_good = reg_rx_good;

        if (tx_stat_avail) {
        	if (tx_din.good) {
				if (tx_din.count == 64) {
					++reg_tx_64;
				} else if (tx_din.count < 128) {
					++reg_tx_65_127;
				} else if (tx_din.count < 256) {
					++reg_tx_128_255;
				} else if (tx_din.count < 512) {
					++reg_tx_256_511;
				} else if (tx_din.count < 1024) {
					++reg_tx_512_1023;
				} else {
					++reg_tx_1024_max;
				}
        	}
        }

        if (rx_stat_avail) {
        	if (rx_din.good) {
                ++reg_rx_good;
                reg_rx_bytes+=rx_din.count;
				if (rx_din.count == 64) {
					++reg_rx_64;
				} else if (rx_din.count < 128) {
					++reg_rx_65_127;
				} else if (rx_din.count < 256) {
					++reg_rx_128_255;
				} else if (rx_din.count < 512) {
					++reg_rx_256_511;
				} else if (rx_din.count < 1024) {
					++reg_rx_512_1023;
				} else {
					++reg_rx_1024_max;
				}
				dummy_last++;
        	}
        }

        tx_stat_avail = tx_status.read_nb(tx_din);
        rx_stat_avail = rx_status.read_nb(rx_din);
    }
}

