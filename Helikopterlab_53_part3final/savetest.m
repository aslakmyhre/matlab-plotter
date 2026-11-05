



experiment = struct();
experiment.data = logdata;
experiment.p1 = p1;
experiment.p2 = p2;

experiment.k_pp = k_pp;
experiment.k_pd = k_pd;
experiment.K_f = k_f;
experiment.v_s0 = v_s0;
experiment.description = ...
    "Aggresiv, p lik -6, -5";
save("part1_task3_aggresiv.mat", "experiment");