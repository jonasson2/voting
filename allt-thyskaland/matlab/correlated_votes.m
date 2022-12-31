function [gpv, gcv] = correlated_votes(nsim, nconst)
  model_params = load('model_params.mat');
  gpv = correlated_partyvotes(nsim, model_params);
  gcv = regressed_const_votes(gpv, nconst);
end

function gpv = correlated_partyvotes(nsim, param)
  for p=1:7
    Z = randnm(nsim, param.Sig(:,:,p), param.mu(:,p));
    gpv(:,p,:) = exp(Z'); %#ok<*AGROW> 
  end
end

function gcv = regressed_const_votes(partyvotes, nconst)
  data = load('regression_params.mat');
  sigma = get_piecewise_poly(data, 'sigma');
  beta = get_piecewise_poly(data, 'beta');
  nland = 16;
  M = beta(partyvotes);
  S = sigma(partyvotes);
  [mu, sig] = lognparam(M, S.^2);
  for l=1:nland
    mul = repmat(mu(l, :, :), nconst(l), 1, 1);
    sigl = repmat(sig(l, :, :), nconst(l), 1, 1);
    gcv{l} = exp(normrnd(mul, sigl));
  end
end
  
function pp = get_piecewise_poly(data, name)
  brk = data.(name + "_breaks");
  val = data.(name + "_values");
  pp = griddedInterpolant(brk, val);
end

