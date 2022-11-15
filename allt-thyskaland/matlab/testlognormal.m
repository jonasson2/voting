function testlognormal()
  d = 16;
  voteShare = linspace(10,40,d);
  voteShare = voteShare/sum(voteShare);
  CoV = linspace(0.6, 0.3, d)/2;
  correl = 0.8;
  runTest(voteShare, CoV, correl, 1000)
end

function runTest(voteShare, CoV, correl, n)
  d = length(voteShare);
  stdev = CoV.*voteShare;
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
