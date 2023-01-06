function [mu, Sig, land_weights, M, V, R, RSD] = generate_2nd_parameters(RSD_par,R)
  % RSD = (a*M + b)% where RSD_par = [a, b]
  % Returns mu, Sig = parameters of underlying normal distribution, and 
  % M, V, R = mean, variance and correlation of the lognormal distribution
  [pv, ~, flokkar, lond] = read_votes();
  total_votes = squeeze(sum(pv,2,'omitnan'));
  land_weights = mean(total_votes./sum(total_votes,2));
  PDS = flokkar=='PDS';
  flokkar(PDS) = [];
  pv(:, PDS, :) = [];
  v_share = pv./sum(pv,2,'omitnan')*100;
  M = genmean(v_share, flokkar, lond);
  V = genvar(M, RSD_par);
  fprintf('\n%s\n', 'Expected values:')
  show(M', '-d2')
  RSD = bundes_RSD(pv);
  fprintf('\n%s\n', 'Correlation:')
  show(R, '-d2')
  R(1:17:end) = 1.0;
  for p = 1:length(flokkar)
    [mu{p},Sig{p}] = lognormal_param2normal(M(p,:), V(p,:), R);
    Sig{p} = Sig{p} + 0.03*diag(diag(Sig{p}));
    min(eig(Sig{p}))
    assert(min(eig(Sig{p})) > 0)
    condsig(p) = round(cond(Sig{p})); %#ok<*AGROW>
    %[min(eig(Sig)), max(eig(Sig))]
  end
  disp('Range of condition numbers of the Sigma matrices:')
  fprintf('  %.1f to %.1f\n', min(condsig), max(condsig))
  mu = cell2mat(mu);
  Sig = reshape(cell2mat(Sig), 16, 16, []);
end

function V = genvar(M, RSD_par)
  %RSD = (42 - 0.63*M)/100;
  RSD = (RSD_par(1)*M + RSD_par(2))/100;
  V = (RSD.*M).^2;
end

function M = genmean(v_share, flokkar, lond)
  avg = mean(v_share(end-2:end, :, :), 'omitnan');
  M = squeeze(avg);
  table1 = array2table(M', VariableNames=flokkar, RowNames=lond);
  writetable(table1, 'table1.xlsx', WriteRowNames=true)
end

function RSD = bundes_RSD(pv)
  bv = sum(pv, 3);
  RSD = std(bv, 'omitnan')./mean(bv, 'omitnan');
end
