0.907::pollution("low"); 0.093::pollution("high").
0.286::smoker.
0.038910505836576::cancer :- pollution("low"), smoker.
0.0::cancer :- pollution("low"), \+smoker.
0.0::cancer :- pollution("high"), smoker.
0.03125::cancer :- pollution("high"), \+smoker.
0.666666666666635::dyspnoea :- cancer.
0.286437246963563::dyspnoea :- \+cancer.
0.999999999999997::xray("positive"); 0.999999959822715::xray("negative") :- cancer.
1.0::xray("positive"); 1.0::xray("negative") :- \+cancer.
