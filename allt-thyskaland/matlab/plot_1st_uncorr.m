function plot_1st_uncorr()
  load constvotes.mat parties lander voteshareC colors
  nparty = length(parties);
  nland = length(lander);
  nyear = size(voteshareC{1},1);

  for l=1:nland
    v{l} = voteshareC{l};
  end
  %
  x = cat(3, v{:});
  x = reshape(x, nyear, []);
  party = repmat(1:nparty, [1, size(x,2)/nparty]);
  wgt = sum(~isnan(x)) - 1;
  nlong = 2;
  LONG = wgt >= nlong;
  x = x(:,LONG);
  wgt = wgt(LONG);
  party = party(LONG);
  m = mean(x, 'omitnan');
  s = std(x, 'omitnan');
  lastslope = [];
  breakpoint = 35:55;
  for bp = breakpoint
    b = broken_line_regress(m, s./m, [0 bp 65], weight=wgt);
    lastslope(end+1) = (b(65) - b(55))/10;
  end
  [~, i] = min(abs(lastslope));
  b = broken_line_regress(m, s./m, [0 breakpoint(i) 65], weight=wgt);
  %b = broken_line([0, 45, 60], [0.46, 0.12, 0.12]);

  clf
  scatter(m, s./m, 10, colors(party,:), 'filled', 'o')
  hold on
  broken_line_plot(b);
  ylim([0, 0.9])
  xlim([0,65])
  set(gca, 'ytick', 0:0.1:0.9)
  ylbl = str2double(get(gca,'yticklabel'));
  set(gca, 'yticklabels', ylbl*100)
  ylabel('Relative standard deviation, %')
  fmt = "Average vote share in constituencies with more than %d results, %%";
  xlabel(sprintf(fmt, nlong));
  large_marker_legend(parties(1:end-1), colors, 10, 'northeast')
  grid on
  tightaxis
  print -dpng uncorr_RSD_by_vs.png
  
  ndec = 4;
  fprintf('Break point: %d\n', breakpoint(i))
  fprintf('Values:\n')
  fprintf('  At 0:  %.*f\n', ndec, b(0));
  fprintf('  At 40: %.*f\n', ndec, b(40));
  fprintf('  At bp: %.*f\n', ndec, b(bp));
  fprintf('  At 60: %.*f\n', ndec, b(60));
  fprintf('Last slope:  %.4f\n', lastslope(i))

  cnames = read_const_names();
  nconst = cellfun(@length, cnames);
  for l=1:nland
    vl = v{l};
    current_parties = find(any(~isnan(vl(end,:,:)),3));
    if l==1
      PARTY_2021 = current_parties;
      parties = parties(PARTY_2021);
    else
      assert(isequal(PARTY_2021, current_parties))
    end
    %PARTY_2021 = intersect(PARTY_2021, dropother);
    CONST_2021 = reshape(any(~isnan(vl(end,:,:)),2), [], 1);
    vlast3 = vl(end-2:end, PARTY_2021, CONST_2021);
    ref_votes{l} = permute(mean(vlast3, 1, "omitnan"), [3,2,1]);
    nnan = sum(isnan(ref_votes{l}(:)));
    if nnan > 0
      fprintf('Filled %d missing values in land %d\n', nnan, l)
    end
    ref_votes{l} = fillmissing(ref_votes{l}, "movmean", 2*nconst(l));
    const_names{l} = string(cnames{l}(CONST_2021));
  end

  breakpoints = b.GridVectors{1}(1:end-1)';
  values = b.Values(1:end-1)';

  save uncorr_model.mat const_names parties ref_votes breakpoints values -mat

end