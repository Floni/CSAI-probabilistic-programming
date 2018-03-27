t(_)::pollution("low"); t(_)::pollution("high").
t(_)::smoker.
t(_)::cancer :- pollution("low"), smoker.
t(_)::cancer :- pollution("low"), \+smoker.
t(_)::cancer :- pollution("high"), smoker.
t(_)::cancer :- pollution("high"), \+smoker.
t(_)::dyspnoea :- cancer.
t(_)::dyspnoea :- \+cancer.
t(_)::xray("positive"); t(_)::xray("negative") :- cancer.
t(_)::xray("positive"); t(_)::xray("negative") :- \+cancer.

%query(pollution(_)).
%query(smoker).
%query(cancer).
%query(dyspnoea).
%query(xray(_)).