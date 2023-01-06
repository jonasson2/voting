function testlognormal()
  d = 16;
  voteShare = linspace(10,40,d);
  voteShare = voteShare/sum(voteShare);
  RSD = linspace(0.6, 0.3, d)/2;
  correl = 0.8;
  runTest(voteShare, RSD, correl, 1000)
end

function runTest(voteShare, RSD, correl, n)
  d = length(voteShare);
  stdev = RSD.*voteShare;
  R = zeros(d,d) + correl;
  R(1:d+1:end) = 1;
  X = lognormal_rand_m(voteShare, stdev, R, n);
  Re = corr(X);
  Se = var(X);
  Me = mean(X);
  Re
  Se
  Me
end
