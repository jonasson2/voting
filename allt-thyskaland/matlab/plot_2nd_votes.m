[pv, cv, flokkar, lond, litir, ar] = read_votes();
flokkar(flokkar=='CDU') = 'CDU/CSU';
set(0, defaultaxeslinewidth=1)
set(0, defaultaxesticklength=[0,0])
figure_positions()
%pv = set_old_linke_to_nan(pv, flokkar, ar);
pv(pv==0) = NaN;
east = 11:16;
west = 1:10;
OTHER = flokkar=="other";
[bv, land_weights] = bundeswide(pv);
%pv(:, PDS, west) = NaN;
vote_share = pv./sum(pv, 2, 'omitnan')*100; % Standardize
vote_plot(bv, litir, flokkar, ar, fig=1)
SEL = ismember(flokkar, ["SPD", "FDP", "Grüne", "Linke", "CDU/CSU"]);
corr_compute(pv, lond, flokkar, litir, SEL, fig=5)
%title_g = 'Sum over all Länder';
%title_l = 'Individual Länder';
[title_g, title_l] = deal('');
pg = CoV_plot(bv, litir, flokkar, title_g, SEL, fig=4);
pl = CoV_plot(vote_share, litir, flokkar, title_l, SEL, fig=3);
pg
pl
fig 2; clf
for land = 1:16
  subplot(4,4,land)
  CoV_plot(vote_share(:,:,land), litir, flokkar, lond{land}, SEL);
  legend off
  xlabel('Avg. vote share')
  set(gca, 'TitleFontWeight', 'normal');
end
tightaxis(4, 4, [5,13], [5,5,5,10])
save_fig()
CoV_par = [round(pl(1)*100)/100, round(pl(2))];

function [bv, land_weights] = bundeswide(pv)
  total_votes = squeeze(sum(pv,2,'omitnan'));
  land_weights = mean(total_votes./sum(total_votes,2));
  bv = sum(pv,3,'omitnan');
  bv(bv==0) = NaN;
  bv = bv./sum(bv, 2, 'omitnan')*100; % Standardize
end

function corr_compute(pv, lond, flokkar, litir, SEL, fig, nr)
  if exist('fig', 'var') && fig=="fig", figure(nr); clf, end
  P = find(SEL);
  hold on
  D = distance_matrix(lond);
  W = 1:10;
  E = 12:16;
  west_dist = D(W,W);
  east_dist = D(E,E);
  for j=1:length(P)
    p = P(j);
    X = pv(:,p,:)./sum(pv, 2, 'omitnan')*100;
    X = squeeze(X);
    X(X==0) = 16;
    CW = corr(X(:,W), rows='pairwise');
    CE = corr(X(:,E), rows='pairwise');
    cew(:,:,j) = corr(X(:,W),X(:,E));
    cbw(:,:,j) = corr(X(:,11), X(:,W));
    cbe(:,:,j) = corr(X(:,11), X(:,E));
    cw(:,:,j) = CW;
    ce(:,:,j) = CE;
    litur = litir(p,:);    
    % scatter(vecl(east_dist),vecl(CE),50,litur,"filled")
    scatter(vecl(west_dist),vecl(CW),50,litur,"filled")
    %
  end
  xlabel('Distance between geographic centers of the Länder, km')
  ylabel('Pairwise correlation')
  grid on
  [~,leg] = legend(flokkar(P), location='southwest');
  legmkr = findobj(leg, 'type', 'patch');
  set(legmkr, markersize=sqrt(50))
  dw = vecl(west_dist);
  de = vecl(east_dist);
  cw = vecl(mean(cw,3));
  ce = vecl(mean(ce,3));
  cew = mean(cew,3);
  cbw = mean(cbw,3);
  cbe = mean(cbe,3);
  vv = [];
  for k=0:100:500
    I = k < dw & dw <= k+100;
    if k==500, I = k < dw; end
    d1 = mean(dw(I));
    v1 = mean(cw(I));
    plot(d1, v1, 'O', linewidth=4, markersize=20, color=rgb('gray'))
    vv = [vv v1];
  end
  axis([0,640,0.50,1])
  set(gca, 'ytick', 0.5:0.1:1)
  %title(['Correlation between vote shares 1990–2021, Länder of former '...
  %  'W-Germany excl. Berlin'])
  %moveTitleUp()
  set(gca, 'TitleFontWeight', 'normal')
  tightaxis([0,0,5,10])
  save_fig()
  show(vv, '-digits:3/')
end 

function p = CoV_plot(vote_share, litir, flokkar, titill, SEL, fig, nr)
  demingpar = 1000;
  vote_share = vote_share(:, SEL, :);
  litir = litir(SEL,:);
  flokkar = flokkar(SEL);
  if exist('fig', 'var') && fig=="fig", figure(nr); clf, end
  nd = ndims(vote_share);
  nflokkar = length(flokkar);
  xp = mean(vote_share, 'omitnan');
  yp = std(vote_share, 0, 'omitnan')./xp*100;
  w = sum(~isnan(vote_share)) - 1;
  xp = xp(:)';
  yp = yp(:)';
  wp = w(:)';
  if nd==3
    grp = repmat(1:nflokkar, 1, 16);
  else
    grp = flokkar;
  end
  % p = polyfit(xp, yp, 1);
  [x,y] = deal([]);
  for i=1:length(w)
    x = [x, repmat(xp(i), 1, wp(i))];
    y = [y, repmat(yp(i), 1, wp(i))];
  end
  xbreak = 40;
  p = demingRegression(x, y, demingpar);
  p0 = polyval(p,0);
  pbreak = polyval(p,xbreak);
  %t = linspace(0,60);
  %yt = CoV_interp(t, c0, c40);
  xmax = 50;
  ymax = max(50, max(yp));
  ymax = 60;
  hold on
  %p = plot(t, yt, color=rgb('darkgray'), linewidth=4);
  gh = plot([0, xbreak, xmax], [p0, pbreak, pbreak], color=rgb('darkgray'), ...
    linewidth=4);
  g = gscatter(xp, yp, grp, litir, [], 30);
  fixcolors(g, 'w')
  ymax = ceil(ymax/5)*5;
  axis([0,xmax,0,ymax])
  set(gca,'xtick', 0:10:xmax)
  set(gca,'ytick', 0:10:ymax)
  legend([g;gh], [flokkar; 'best fit'], NumColumns=2, location="northeast")
  xlabel('Vote share, average over all elections, %')
  ylabel('Coefficent of variation, %')
  grid on
  if ~isempty(titill)
    title(titill);
    moveTitleUp()
    topmargin = 20; 
  else
    topmargin = 0;
  end
  if exist('nr', 'var')
    tightaxis([0,0,3,topmargin])
    save_fig()
  end
end

function vote_plot(bv, litir, flokkar, ar, fig, nr)
  if fig=="fig", figure(nr); clf; end
  hold on
  colororder(litir)
  plot(bv, linew=3.5)
  set(gca, 'xticklabels', ar)
  axis([1,9,0,55])
  ytick = get(gca, 'ytick');
  set(gca, 'yticklabels', ytick)
  ylabel('Vote share, %')
  legend(flokkar(1:size(bv,2)), NumColumns=2, Location='northeast')
  grid on
  %title('Share of votes summed over all Länder');
  %moveTitleUp()
  tightaxis([0,0,4,0])
  print -dpng fig1
end

function save_fig()
  tab = {
    1, 'fig1'
    2, 'fig2'
    3, 'fig3a'
    4, 'fig3b'
    5, 'fig4'
  }';
  figs = dictionary(tab{:});
  nr = gcf().Number;
  print(figs(nr), '-dpng')
end

function figure_positions()
  w = 440;
  h = 400;
  wnarrow = 340;
  hextra = round(1.8*h);
  wextra = round(1.3*w);
  %for i=1:6, figure(i); end
  figpos(1, 'left', h, w, h)
  figpos(2, 'right', 'bottom', wextra, hextra)
  figpos(5, 'left', 0, w, h)
  figpos(3, w, h, wnarrow, h)
  figpos(4, w, 0, wnarrow, h)
end

function fixcolors(gv, color)
  for g=gv(:)'
    g.MarkerSize = g.MarkerSize/4;
    g.Marker = 'o';
    g.MarkerFaceColor = g.Color;
    g.MarkerEdgeColor = color;    
  end
end

function moveTitleUp()
  t = get(gca,'title');
  t.Position(2) = t.Position(2) + diff(ylim)*0.005;
end

function v = vecl(A) % strictly lower vec
  n = size(A,2);
  v = [];
  for i=1:n
    v = [v; A(i+1:end, i)];
  end
end

% Note about marker sizes:
% The default marker of gscatter is . (dot) and the size is measured in points
% of a corresponding full-height letter (same as for plot). A suitable size
% might be ~20. Marker o has a diameter 3.41 times the diameter of dot (or
% 1/2.93). With scatter the marker size is measured as the area of a square with
% the same diameter as the o marker.



