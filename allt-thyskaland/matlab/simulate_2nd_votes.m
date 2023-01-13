function [pv_out, bv_out] = simulate_2nd_votes(n, CoV_par)
  if ~exist('CoV_par', 'var'), CoV_par = [-0.54 40]; end
  if ~exist('n', 'var'), n = 1000; end
  [mu, Sig, land_weights] = generate_2nd_parameters(CoV_par);
  nparty = length(mu);
  for i=1:nparty
    X = mvnrnd(mu{i}, Sig{i}, n);
    VS = exp(X);
    pv(:,i,:) = VS; %#ok<*AGROW> 
    bv(:,i) = sum(VS.*land_weights, 2);
  end
  if nargout == 0
    check_simulation(pv, bv, CoV_par)
  else
    pv_out = pv;
    bv_out = bv;
  end
end

function check_simulation(pv, bv, CoV_par)
  [~, ~, flokkar, lond] = read_votes();
  flokkar(flokkar=="PDS") = [];
  [~, ~, land_weights, M, V, ~, CoV] = generate_2nd_parameters(CoV_par);
  data_avg = sum(land_weights.*M, 2);
  avg_pv = squeeze(mean(pv))';
  SD_pv = squeeze(std(pv))';
  CoV_pv = SD_pv./avg_pv * 100;
  avg_bv = mean(bv)';
  SD_bv = std(bv)';
  CoV_bv = SD_bv./avg_bv * 100;
  disp("CoV of party_votes by land:")
  %show(CoV_pv')
  disp("CoV of party votes:")
  displaytable(array2table(CoV_pv, VariableNames=flokkar, RowNames=lond), 2)
  t = table();
  t.("Data total vote share") = data_avg;
  t.("Sim. total vote share") = mean(bv)';
  t.("Data avg CoV") = sum(sqrt(V)./M.*land_weights, 2)*100;
  t.("Sim avg CoV") = sum(CoV_pv'.*land_weights, 2);
  t.("Data totals CoV") = 100*CoV';
  t.("Sim totals CoV")   = CoV_bv;
  t.Properties.RowNames = flokkar;
  displaytable(t,1)
end
