clear c S
ro = 0.8;
for i=1:10000
  mu = [3,3];
  Sig = [1 ro; ro 1];
  for k=3:20
    X = mvnrnd(mu, Sig, k);
    c(i,k-2) = corr(X(:,1), X(:,2));
  end
end
S = rms(c-ro);
S.*((1:18).^0.5)