function [mu, Sig, land_weights, M, V, CoV] = generate_2nd_parameters(CoV_par)
  [pv, ~, flokkar, lond] = read_votes();
  total_votes = squeeze(sum(pv,2,'omitnan'));
  land_weights = mean(total_votes./sum(total_votes,2));
  PDS = flokkar=='PDS';
  flokkar(PDS) = [];
  pv(:, PDS, :) = [];
  v_share = pv./sum(pv,2,'omitnan')*100;
  M = genmean(v_share, flokkar, lond);
  V = genvar(M, CoV_par);
  CoV = bundes_CoV(pv);
  R = gencorr(lond);
  for p = 1:length(flokkar)
    [mu{p},Sig{p}] = lognormal_param2normal(M(p,:), V(p,:), R);
    assert(min(eig(Sig{p})) > 0)
    condsig(p) = round(cond(Sig{p})); %#ok<*AGROW>
    %[min(eig(Sig)), max(eig(Sig))]
  end
  disp('Range of condition numbers of the Sigma matrices:')
  fprintf('  %.1f to %.1f\n', min(condsig), max(condsig))
end

function V = genvar(M, CoV_par)
  %CoV = (42 - 0.63*M)/100;
  CoV = (CoV_par(2) + CoV_par(1)*M)/100;
  V = (CoV.*M).^2;
end

function M = genmean(v_share, flokkar, lond)
  avg = mean(v_share(end-2:end, :, :), 'omitnan');
  M = squeeze(avg);
  table1 = array2table(M', VariableNames=flokkar, RowNames=lond);
  writetable(table1, 'table1.xlsx', WriteRowNames=true)
end

function CoV = bundes_CoV(pv)
  bv = sum(pv, 3);
  CoV = std(bv, 'omitnan')./mean(bv, 'omitnan');
end

function R = gencorr(lond)
  D = distance_matrix(lond);
  R = zeros(16,16);
  for i=1:10
    for j=1:i-1
      if D(i,j) < 100
        R(i,j) = 0.95;
      elseif D(i,j) < 200
        R(i,j) = 0.94;
      elseif D(i,j) < 300
        R(i,j) = 0.93;
      elseif D(i,j) < 400
        R(i,j) = 0.92;
      elseif D(i,j) < 500
        R(i,j) = 0.91;
      else
        R(i,j) = 0.90;
      end
    end
  end
  for i=12:16
    for j=12:i-1
      R(i,j) = 0.86;
    end
  end
  SBB = 8:10;
  other7 = 1:7;
  TSB = [13,15,16];
  other2 = [12,14];
  Berlin = 11;
  R(TSB, SBB) = 0.63;
  R(TSB, other7) = 0.72;
  R(other2, SBB) = 0.74;
  R(other2, other7) = 0.82;
  R(Berlin, other7) = 0.95;
  R(Berlin, SBB) = 0.88;
  R(TSB, Berlin) = 0.75;
  R(other2, Berlin) = 0.84;
  %R()
  R = R + tril(R,-1)';
  R(1:17:16^2) = 1;
  %show(R, '-b2')
  R = R - 0.02;
  R(1:17:16^2) = 1;
end
