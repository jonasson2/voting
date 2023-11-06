function X = logistic_normal_rand(mu, Sig, n)
  Y = mvnrnd(mu, Sig, n);
  W = exp(Y);
  XN = 1./(1 + sum(W, 2));
  X = XN.*W;
  X(:,end+1) = XN;
end
