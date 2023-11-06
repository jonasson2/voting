function [m, v] = logistic_normal_param(M, V, R)
  M = M(:);
  V = V(:);
  sig2 = log(1 + V./M.^2);
  sig = sqrt(sig2);
  mu = log(M) - sig2/2;
  e = sqrt(sig2 - 1);
  D = diag(sig);
  C = log((e*e').*R + 1);
  m = mu(1:end-1) - mu(end);
  v = sig2(1:end-1) + sig2(end) - 2*C(1:end-1, end);
end