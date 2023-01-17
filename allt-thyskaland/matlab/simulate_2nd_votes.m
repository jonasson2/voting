function [pv_out, bv_out] = simulate_2nd_votes(n, RSD_par)
  if ~exist('RSD_par', 'var'), RSD_par = [-0.54 40]; end
  if ~exist('n', 'var'), n = 1000; end
  [mu, Sig, land_weights] = generate_2nd_parameters(RSD_par);
  nparty = length(mu);
  for i=1:nparty
    X = mvnrnd(mu{i}, Sig{i}, n);
    VS = exp(X);
    pv(:,i,:) = VS; %#ok<*AGROW> 
    bv(:,i) = sum(VS.*land_weights, 2);
  end
  if nargout == 0
    check_simulation(pv, bv, RSD_par)
  else
    pv_out = pv;
    bv_out = bv;
  end
end

function check_simulation(pv, bv, RSD_par)
  [~, ~, flokkar, lond] = read_votes();
  flokkar(flokkar=="PDS") = [];
  [~, ~, land_weights, M, V, ~, RSD] = generate_2nd_parameters(RSD_par);
  data_avg = sum(land_weights.*M, 2);
  avg_pv = squeeze(mean(pv))';
  SD_pv = squeeze(std(pv))';
  RSD_pv = SD_pv./avg_pv * 100;
  avg_bv = mean(bv)';
  SD_bv = std(bv)';
  RSD_bv = SD_bv./avg_bv * 100;
  disp("RSD of party_votes by land:")
  %show(RSD_pv')
  disp("RSD of party votes:")
  displaytable(array2table(RSD_pv, VariableNames=flokkar, RowNames=lond), 2)
  t = table();
  t.("Data total vote share") = data_avg;
  t.("Sim. total vote share") = mean(bv)';
  t.("Data avg RSD") = sum(sqrt(V)./M.*land_weights, 2)*100;
  t.("Sim avg RSD") = sum(RSD_pv'.*land_weights, 2);
  t.("Data totals RSD") = 100*RSD';
  t.("Sim totals RSD")   = RSD_bv;
  t.Properties.RowNames = flokkar;
  displaytable(t,1)
end
