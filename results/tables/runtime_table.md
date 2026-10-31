### Running time and error in three tests (Table 1 analogue)

Sequential runs at the default configuration (200 nodes, ratio 0.2, R = 40 m). Python/NumPy timings on this machine; not comparable with the paper's MATLAB timings. 'Positioning accuracy (%)' is not reported because the paper does not define it (Q15).

| Algorithm | Test 1 time (s) | Test 1 norm. error | Test 1 error (m) | Test 2 time (s) | Test 2 norm. error | Test 2 error (m) | Test 3 time (s) | Test 3 norm. error | Test 3 error (m) | Mean time (s), all runs | 95% CI ± | Runs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DV-HOP | 0.080 | 0.317 | 12.691 | 0.056 | 0.308 | 12.334 | 0.056 | 0.316 | 12.644 | 0.058 | 0.005 | 23 |
| HCMCDV-HOP | 0.058 | 0.392 | 15.682 | 0.051 | 0.360 | 14.402 | 0.053 | 0.414 | 16.569 | 0.054 | 0.003 | 23 |
| HCMSPSO-DV-HOP | 2.714 | 0.269 | 10.744 | 2.751 | 0.268 | 10.724 | 2.753 | 0.290 | 11.593 | 2.735 | 0.018 | 23 |
