#include <stdio.h>
#include "axi_lite.hpp"

t_tx_status frames[] = {
  {64, 1, 0, 0, 0, 0, 0},
//  {65, 1, 0, 0, 0, 0, 0}
};

extern ap_uint<64> tx_64;
extern ap_uint<64> tx_65_127;
extern ap_uint<64> tx_128_255;
extern ap_uint<64> tx_256_511;
extern ap_uint<64> tx_512_1023;
extern ap_uint<64> tx_1024_max;

#define FRAMES_CNT sizeof(frames) / sizeof(t_tx_status)

int main()
{
  int j;

  hls::stream<t_tx_status> tx_status;

  for (j = 0; j < FRAMES_CNT; j++) {
    tx_status.write(frames[j]);
    axi_lite(tx_status);
  }

//  axi_lite(tx_status, &tx_64, &tx_65_127, &tx_128_255, &tx_256_511, &tx_512_1023, &tx_1024_max);
  //if ((tx_64 != 1) || (tx_65_127 != 1)) {
  if ((tx_64 != 1)) {
	  return 1;
  } else {
	  return 0;
  }
}

