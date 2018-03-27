0.94::pollution("low"); 0.06::pollution("high").
0.32::smoker.
0.0::cancer :- pollution("low"), smoker.
0.015151515151515::cancer :- pollution("low"), \+smoker.
0.0::cancer :- pollution("high"), smoker.
0.0::cancer :- pollution("high"), \+smoker.
0.999999990569249::dyspnoea :- cancer.
0.303030303030303::dyspnoea :- \+cancer.
0.104684276717702::xray("positive"); 0.999999999725664::xray("negative") :- cancer.
1.0::xray("positive"); 1.0::xray("negative") :- \+cancer.
