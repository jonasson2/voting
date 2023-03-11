function [mu, Sig] = lognormal_param2normal(M, V, R)
  % Return parameters of multivariate normal distribution corresponding to the
  % lognormal distribution with mean M, variance V and correlation matrix R.
  assert(all(diag(R)==1))
  M = M(:);
  if length(V)==1
    V = repmat(V, size(M));
  else
    V = V(:);
  end
  sig2 = log(1 + V./M.^2); % cf Wikipedia
  mu = log(M) - sig2/2;
  sig = sqrt(sig2);
  % For following, see question 6853 on stats.stackexchange
  e = sqrt(exp(sig2) - 1);
  Rnormal = log((e*e').*R + 1)./(sig*sig');
  D = diag(sig);
  Sig = D*Rnormal*D;
end
