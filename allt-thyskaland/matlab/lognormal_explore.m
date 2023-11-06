clear all
n = 9;
rng(1)
B = 1000000;
for i=1:1000000
  if mod(i,1000)==1, fprintf('i=%d\n',i), end
  e = exp(1);
  x = lognrnd(0, 1, n, 1);
  M(i) = logmean(x);
  V(i) = logvar(x);
  meanx(i) = mean(x);
  varx(i) = var(x);
  %bb = bootstrap_bias(x, B, @logvar);
  %Vbeb(i) = V(i) + bb;
  Vbeb(i) = 0;
  %   fit = lognfit(x);
  %   par = mle(x, distribution='logn');
  %   [~, varfit(i)] = lognmoments(fit(1), fit(2));
  %   [~, mlefit(i)] = lognmoments(par(1), par(2));
end
fprintf('x er log-normal og y er transformerað í normal\n')
fprintf('M og V eru reiknuð (fræðilega) út frá mean(y) og var(y))\n')
fprintf('mean(M) = %.3f, std(M) = %.3f\n',   mean(M), std(M))
fprintf('mean(V) = %.3f, std(V) = %.3f\n', mean(V), std(V));
fprintf('mean(mean-x) = %.3f, std(mean-x) = %.3f\n', mean(meanx), std(meanx))
fprintf('mean(var-x)  = %.3f, std(var-x)  = %.3f\n', mean(varx), std(varx))
fprintf('mean(Vbeb)  = %.3f, std(Vbeb)  = %.3f\n', mean(Vbeb), std(Vbeb))
% fprintf('mean(mlefit)  = %.3f, std(mlefit)  = %.3f\n', mean(mlefit), std(mlefit))

fprintf('rétt meðaltal = %.3f\n', sqrt(e))
fprintf('réttur varíans = %.3f\n', (e-1)*e)

function [M, V] = lognmoments(mu, sig)
  M = exp(mu + sig.^2/2);
  V = (exp(sig) - 1).*M.^2;
end

function boot_est_bias = bootstrap_bias(x, B, s)
  n = length(x);
  y = x(randi(n, n, B));
  boot_est_par = mean(s(y));
  boot_est_bias = boot_est_par - s(x);
end

function M = logmean(x)
  y = log(x);
  mu = mean(y);
  sig = std(y);
  M = exp(mu + sig.^2/2);
end

function V = logvar(x)
  y = log(x);
  mu = mean(y);
  sig = std(y);
  [~, V] = lognmoments(mu, sig);
end  

% The result is that computing V via sigma(y) is slightly biased but has a
% considerably lower variance than computing it directly from the data.
% For M however, an unbiased result is obtained by computing the mean of
% the data and there is no significant variance-difference compared with 
% computation via mu(y).