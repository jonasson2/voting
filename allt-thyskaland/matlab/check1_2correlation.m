function check1_2correlation()
  nconst = [11, 6, 30, 2, 64, 22, 15, 38, 46, 4, 12, 10, 6, 16, 9, 8];
  [gpv, gcv] = correlated_votes(1000, nconst);
  for l=1:16
    for p=1:7
      correl(l,p) = mean(corr(vec(gpv(l,p,:)), squeeze(gcv{l}(:,p,:))'));
    end
  end
  fprintf('Mean simulated correlation: %.2f\n', mean(correl, 'all'))
end

function v = vec(x)
  v = x(:);
end