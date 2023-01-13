function count_outliers(varargin)
  fig = getKeywordParams(varargin, figure=6);
  if ~exist("figure", "var"), fig = 6; end
  figure(fig); clf
  data = load('regression_params.mat');
  [pv,I] = sort(data.Pall);
  cv = data.Call(I);
  beta = get_piecewise_poly(data, "beta");
  sigma = get_piecewise_poly(data, "sigma");
  M = beta(pv);
  S = sigma(pv);
  outliertable(M(pv>5), S(pv>5), cv(pv>5));
  intervals = {
    [0, 5]
    [5, 10]
    [10, 20]
    [20, 30]
    [30, 40]
    [40, 60]
  };
  figpos('PM', 'r', 'b', 0.7, 0.7)
  nsets = length(intervals);
  for k=1:nsets
    I = intervals{k};
    [a, b] = deal(I(1), I(2));
    set = a <= pv & pv < b;
    mid = (a + b)/2;
    subplot(2, 3, k)
    compare(M(set), S(set), beta(mid), sigma(mid), cv(set), I)
  end
  tightaxis(2, 3, [10,20], [0, 13, 0, 0])
end

function outliertable(M, S, constvotes)
  n = length(M);
  V = S.^2;
  [mu, sig] = lognparam(M, V);
  disp("            Ndata  Nnormal  Nlognormal")
  for a = [-4, -3, -2, 2, 3, 4, 5, 6, 7, 8, 9]
    if a < 0
      hdr = sprintf("< M – %d×S", -a);
      ndata = sum(constvotes < M + a*S);
      nnorm = round(n*normcdf(a));
      nlogn = round(sum(logncdf(M + a*S, mu, sig)));
    else
      hdr = sprintf("> M + %d×S", a);
      ndata = sum(constvotes > M + a*S);
      nnorm = round(n*normcdf(a, 'upper'));
      nlogn = round(sum(logncdf(M + a*S, mu, sig, 'upper')));
    end
    fprintf('%s:  %4d   %4d     %4d\n', hdr, ndata, nnorm, nlogn)
  end
end

function compare(M, S, M0, S0, cv, I)
  [mu0, sig0] = lognparam(M0, S0^2);
  %[a0, b0] = gamparam(M0, S0.^2);
  z = (cv - M)./S;
  y = z*S0 + M0;
  t0 = round(min(y));
  if t0 < 5, t0=0; end
  t1 = round(M0 + 4*S0);
  t = linspace(t0, t1, 200);
  sb = sulubreidd(t1 - t0);
  sulur = sulurit(y, sb, 'þétti');
  hold on
  pdf = lognpdf(t, mu0, sig0);
  ymax = max(max(pdf), max(sulur.haed));
  plot(t, pdf, linewidth=4.0, color=[rgb('tomato') 0.6])
  xlim([t0, t1])
  ylim([0, ymax*1.2])
  %plot(t, gampdf(t, a0, b0), LineWidth=2.0, color=rgb('green'))
  plot(t, normpdf(t, M0, S0), linewidth=4.0, color=[rgb('dodgerblue') 0.6])
  legend('data', 'lognormal', 'normal',location='ne')
  ax = get(gcf, "CurrentAxes");
  ax.YTick = [];
  text1 = sprintf("Partyvote interval %d%%–%d%%", I(1), I(2));
  text2 = sprintf("Number of data points %d", length(M));
  annotate({text1, text2}, 'nw')
  xlabel({'Constituency votes (%, transformed to', ...
    'midpoint of partyvote interval)'})
  set(gca,'XTickLabelRotation', 0)
  box on
end

function pp = get_piecewise_poly(data, name)
  brk = data.(name + "_breaks");
  val = data.(name + "_values");
  pp = griddedInterpolant(brk, val);
end

function b = sulubreidd(w)
  if w < 10,  b = 0.5;
  elseif w <= 20, b = 1;
  elseif w <= 35, b = 2;
  elseif w <= 50, b = 3;
  else, b = 4;
  end
end
