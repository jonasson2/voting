%#ok<*AGROW,*UNRCH,*ASGLU,*NASGU>
function plot_1st_votes()
  set(0, 'defaultaxeslinewidth', 0.8)
  BRK = [15, 25, 35, 50];
  set(0, 'defaultaxesticklength', [0,0])
  [partyvotes, constvotes_raw, parties, lander,colors,yr] = read_votes();
  partyvotes(partyvotes==0) = nan;
  mkrsiz = 8;
  nland = length(lander);
  nparty = length(parties);
  for l=1:nland
    for p=1:nparty
      constvotes{l}(:,p,:) = constvotes_raw{p}{l};
    end
  end
  votesum = sum(partyvotes,2,'omitnan');
  voteshareP = partyvotes./votesum*100;
  voteshare_mean = squeeze(mean(voteshareP(end-2:end,:,:),'omitnan'));
  for l=1:nland
    votesum = sum(constvotes{l}, 2, 'omitnan');
    V = constvotes{l}./votesum*100;
    V(V==0) = nan;
    voteshareC{l} = V;
  end
  save constvotes.mat voteshareC parties lander colors -mat

  % DROP PDS AND AfD FOR THE REST OF THIS PROCEDURE
  DROP = ismember(parties, ["PDS", "AFD"]);
  voteshareP(:,DROP,:) = [];
  for l=1:nland
    voteshareC{l}(:,DROP,:) = [];
  end
  parties(DROP) = [];
  nparty = nparty - sum(DROP);
  colors(DROP, :) = [];

  % PLOT CONSTITUENCY VOTES ACCORDING TO PARTY VOTES FOR EACH LAND
  annotate(margin=[3,1])
  figure(1); clf
  figpos('SM', 'l', 'b', 0.5, 1)
  clear pvotes_vec
  breaks = BRK;
  corrtab = zeros(nland, nparty);
  for l=1:nland
    pvotes_vec{l} = [];
    cvotes_vec{l} = [];
    stdevs{l} = [];
    subplot(4,4,l)
    hold on
    for p=nparty:-1:1
      P = voteshareP(:,p,l);
      C = squeeze(voteshareC{l}(:,p,:));
      C(C==0) = nan;
      %C = C;
      [Pvec{l,p}, Cvec{l,p}] = expand(P,C);
      pvotes{l}(:,p) = P;
      stdevs{l}(:,p) = std(C, 0, 2, 'omitnan');
      pvotes_vec{l} = [pvotes_vec{l}; Pvec{l,p}];
      cvotes_vec{l} = [cvotes_vec{l}; Cvec{l,p}];
      plot(Pvec{l,p}, Cvec{l,p}, '.', color=colors(p,:), markersize=mkrsiz)
      wgt = sum(~isnan(C));
      OK = wgt>=3;
      C = C(:,OK);
      wgt = wgt(OK);
      P = detrend(P, 'omitnan');
      C = detrend(C, 'omitnan');
      correl = corr(P, C, rows="pairwise");
      corrtab(l,p) = sum(wgt.*correl/sum(wgt));
    end
    xlabel('Party vote share (%)')
    ylabel('Constituency vote share (%)')
    vmax = max(50, max(pvotes_vec{l}) + 1);
    setaxis(vmax, 0, 80)
    annotate(lander(l), "NW")
    Pl = pvotes_vec{l};
    Cl = cvotes_vec{l};
    [bstd,resrms(l)] = broken_line_fit_and_plot(Pl, Cl, breaks, zero=true);
    label_values(@(x)bstd(x), "cvs", digits=0, resrms=resrms(l))
    grid on
    box on
  end
  fmt = "Average partyvote–const.vote correlation = %.2f\n";
  cor = mean(corrtab, 'all');
  fprintf(fmt, cor)
  fprintf("Average residual RMS = %.1f\n\n", mean(resrms))
  tightaxis(4,4,[7,7],[4,4,0,0])
  print -dpng cv-by-pv+party+land.png

  % PLOT STANDARD DEVIATIONS OF CONSTITUENCY VOTE SHARE FOR EACH LAND
  figure(2), clf
  figpos('SM', 'r', 'b', 0.5, 1)
  for l=1:nland
    ymax = -inf;
    ymin = inf;
    subplot(4,4,l); hold on
    for p=nparty:-1:1
      x = pvotes{l}(:,p);
      y = stdevs{l}(:,p);
      plot(x, y, '.', color=colors(p,:), markersize=mkrsiz*1.4)
      ymin = min(ymin, min(y));
      ymax = max(ymax, max(y));
    end
    xlabel('Party vote share (%)')
    ylbl = 'SD of constituency vote share (%)';
    ymin = 0;
    if lander(l)=="Berlin", ymax=17; else, ymax=9; end
    ylabel(ylbl)
    vmax = max(50, max(pvotes_vec{l}) + 1);
    setaxis(vmax, ymin, ymax)
    annotate(lander(l), "NW")
    I = ~isnan(stdevs{l});
    pf = polyfit_and_plot(pvotes{l}(I), stdevs{l}(I), 1);
    label_values(@(x) polyval(pf, x), "SD");
    grid on
    box on
  end
  tightaxis(4,4,[7,7],[4,4,0,0])
  print -dpng cvSD-by-pv+party+land.png

  % PLOT CONSTITUENCY VOTES ACCORDING TO PARTY VOTES FOR WHOLE GERMANY
  figure(3), clf
  figpos('SM', 'r', 'b', 0.4, 0.5)
  [Pall, Party] = combine_lander(Pvec);
  Call = combine_lander(Cvec);
  J = randperm(length(Pall));
  mkrarea = (1.5 * mkrsiz*0.293)^2;
  scatter(Pall(J), Call(J), mkrarea, colors(Party(J),:), 'filled', 'o')
  hold on
  grid on
  box on
  xlabel('Party vote share (%)')
  ylabel('Constituency vote share (%)')
  [bcvs,resrms] = broken_line_fit_and_plot(Pall, Call, BRK, zero=true ...
    ,                                      top=true, linewidth=6);
  label_values(@(x) bcvs(x), "cvs", resrms=resrms)
  residuals = Call - bcvs(Pall);
  setaxis(60, 0, max(Call))
  large_marker_legend(parties, colors, 10)
  tightaxis()
  print -dpng cv-by-pv+party.png

  % PLOT CONSTITUENCY VOTES ACCORDING TO PARTY VOTES AND PARTY
  figure(4), clf
  figpos('SM', 'l', 't', 0.3, 0.8)
  for p=1:nparty - 1
    subplot(3,2,p)
    J = Party==p;
    hold on
    plot(Pall(J), Call(J), '.', color=colors(p,:), markersize=mkrsiz*0.7)
    [bparty, rrms] = broken_line_fit_and_plot(Pall(J), Call(J), BRK, zero=true);
    label_values(@(x) bparty(x), "cvs", resrms=rrms, values=[10,20])
    xlabel('Party vote share (%)')
    ylabel('Constituency vote share (%)')
    annotate(parties(p), 'NW')
    box on
    grid on
  end
  tightaxis(3,2)
  print -dpng cv-by-pv+party-panels.png

  % CALCULATE RESIDUALS, OUTLIERS AND SKEWNESS
  d = 5;
  k = 0;
  clear V R
  for vsi = 0:d:50
    k = k + 1;
    if vsi >= 50
      I = vsi <= Pall;
    else
      I = vsi <= Pall & Pall <= vsi + d;
    end
    res = residuals(I);
    R(k) = rms(residuals(I));
    V(k) = mean(Pall(I));
    OUT = isoutlier(res, 'grubbs');
    ntotal = length(res);
    noutlier = sum(OUT);
    %res = res(~OUT);
    skew(k) = skewness(res, 1);
    p = normcdf(-skew(k));
    fmt = 'PVS %4.1f%%: n=%4d, #outliers=%2d, skewness=%4.1f, p=%.3f\n';
    fprintf(fmt, V(k), ntotal, noutlier, skew(k), p)
  end

  % PLOT SKEWNESS
  figure(7), clf
  figpos('PM', 'l', 'top', 0.4, 0.5)
  plot(V, skew, '.', markersize=20)
  xlabel('Party votes (%)')
  ylabel('Skewness')
  tightaxis()
  % currently not saved to file

  % PLOT RESIDUAL RMS ACCORDING TO PARTY VOTES FOR WHOLE GERMANY
  figure(5), clf
  hold on
  figpos('SM', 'r', 0.4, 0.2, 0.3)
  plot(V, R, '.', color=rgb("orangered"), markersize=30)
  ymax = 8;
  axis([0,55,0,ymax])
  bstd = broken_line_fit_and_plot(V, R, 20, zero=true);
  grid on
  box on
  xlabel('Party vote share (%)')
  ylabel('Model residual RMS')
  tightaxis()
  print -dpng resrms-by-pv.png

  % DISPLAY MODEL PARAMETERS ON SCREEN AND WRITE THEM TO FILE
  disp(' ')
  disp('MODEL:')
  disp('    CVS = l(PVS) + eps')
  disp('  where eps ~ N(0,sig), l and sig are piecewise linear, and:')
  clear beta_breaks sigma_breaks beta_values sigma_values
  beta_breaks = [0, BRK, 100];
  for k = 1:length(beta_breaks)
    p = beta_breaks(k);
    beta_values(k) = round(bcvs(p), 1);
    fprintf('    l(%d) = %.1f\n', p, beta_values(k));
  end
  sigma_breaks = [0, 20, 100];
  sigmean20 = mean(bstd(V(V>=20)));
  sigma_values(1) = 0;
  sigma_values(2:3) = round(sigmean20, 1);
  for k = 1:3
    fprintf('    sig(%d) = %.1f\n', sigma_breaks(k), sigma_values(k))
  end
  votes_all = sum(partyvotes(end,:,:),'omitnan');
  save regression_params.mat -regexp '.*_breaks|.*_values|.*all'

  % PLOT RESIDUALS AND DISPLAY OUTLIER TABLE
  count_outliers(figure=6)
  print -dpng sulurit.png

  % SIMULATE VOTES AND FIND CORRELATION BETWEEN SIMULATED PARTY- AND CONST.VOTES
  check1_2correlation()
end

function setaxis(xmax, ymin, ymax)
  set(gca, 'xlim', [0, xmax]);
  set(gca, 'xtick', 0:10:xmax);
  ylim([ymin, ymax])
  if ymax > 30
    set(gca, 'ytick', ymin:10:ymax)
  elseif ymax > 10
    set(gca, 'ytick', ymin:2:ymax)
  else
    set(gca, 'ytick', ymin:1:ymax)
  end
end

function [x,y] = expand(X,Y)
  [m,n] = size(Y);
  x = reshape(repmat(X, 1, n), m*n, 1);
  y = Y(:);
  I = isnan(x) | isnan(y);
  x(I) = [];
  y(I) = [];
end

function c = polyfit_and_plot(x, y, n, varargin)
  [TOP, lw] = getKeywordParams(top=true, linewidth=4);
  xmax = gca().XLim(2);
  c = polyfit(x, y, n);
  t = linspace(0, xmax);
  tval = polyval(c, t);
  [lw, clr] = linewidth_and_color(top=TOP);
  ph = plot(t, tval, color=clr, linewidth=lw);
  if ~TOP
    uistack(ph, 'bottom')
  end
end

function label_values(fun, ftxt, varargin)
  [dig, resrms, values] = getKeywordParams(digits=1, ...
    resrms=[], values = [10,40]);
  val1 = fun(values(1));
  val2 = fun(values(2));
  txt{1} = sprintf("%s(%d) = %.*f%%", ftxt, values(1), dig, val1);
  txt{2} = sprintf("%s(%d) = %.*f%%", ftxt, values(2), dig, val2);
  if ~isempty(resrms)
    txt{3} = "residual RMS = " + sprintf("%.*f%%", dig+1, resrms);
  end
  annotate(txt, "SE")
end

function [xvec,pvec] = combine_lander(X)
  [nl, np] = size(X);
  xvec = [];
  pvec = [];
  for p=1:np
    xp = X{1,p};
    xvec = [xvec; xp];
    pvec = [pvec; repmat(p, length(xp), 1)];
    for l=2:nl
      xp = X{l,p};
      xvec = [xvec; xp];
      pvec = [pvec; repmat(p, length(xp), 1)];
    end
  end
end
