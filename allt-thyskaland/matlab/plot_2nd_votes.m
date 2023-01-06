%#ok<*AGROW> 
[partyvotes, ~, parties, lander, colors, ar] = read_votes();
parties(parties=='CDU') = 'CDU/CSU';
set(0, defaultaxeslinewidth=1)
set(0, defaultaxesticklength=[0,0])
set(0, defaultaxesxgrid='on', defaultaxesygrid='on')
set(0, defaultaxesbox='on')
figure_positions()
%pv = set_old_linke_to_nan(pv, flokkar, ar);
partyvotes(partyvotes==0) = NaN;
east = 11:16;
west = 1:10;
OTHER = parties=="other";
bv = bundeswide(partyvotes);
%pv(:, PDS, west) = NaN;
votesum = sum(partyvotes, 2, 'omitnan');
vote_share = partyvotes./votesum*100; % Standardize
vote_plot(bv, colors, parties, ar, fig=1)
SEL = ismember(parties, ["SPD", "FDP", "Grüne", "Linke", "CDU/CSU"]);
R = corr_compute(partyvotes, lander, SEL, fig=5);
%title_g = 'Sum over all Länder';a
%title_l = 'Individual Länder';
[title_g, title_l] = deal('');
pg = RSD_plot(bv, colors, parties, title_g, SEL, fig=4);
pl = RSD_plot(vote_share, colors, parties, title_l, SEL, fig=3);
fmt = "%s:\nRSD = %.0f - %.2f×(voteshare)\n";
fprintf(fmt, 'Whole-Germany RSD', pg(2), -pg(1))
fprintf(fmt, 'RSD in each Land', pl(2), -pl(1))
fig 2; clf
for land = 1:16
  subplot(4,4,land)
  RSD_plot(vote_share(:,:,land), colors, parties, lander{land}, SEL);
  legend off
  xlabel('Avg. vote share')
  set(gca, 'TitleFontWeight', 'normal');
end
tightaxis(4, 4, [5,13], [5,5,5,10])
save_fig()
RSD_par = [round(pl(1)*100)/100, round(pl(2))];
[mu, Sig] = generate_2nd_parameters(RSD_par, R);
colors(parties=="PDS", :) = [];
parties(parties=="PDS") = [];
parties = cellstr(parties);
lander = cellstr(lander);
votesum = reshape(votesum(end,:,:), 1, []);
save model_params.mat votesum mu Sig lander parties colors

function [bv, land_weights] = bundeswide(pv)
  total_votes = squeeze(sum(pv,2,'omitnan'));
  land_weights = mean(total_votes./sum(total_votes,2));
  bv = sum(pv,3,'omitnan');
  bv(bv==0) = NaN;
  bv = bv./sum(bv, 2, 'omitnan')*100; % Standardize
end

function R = corr_compute(pv, lander, SEL, fig, nr)
  if exist('fig', 'var') && fig=="fig", figure(nr); clf, end
  P = find(SEL);
  hold on
  D = distance_matrix(lander);
  clear cew cbw cbe cw ce C w
  for k=1:length(P)
    p = P(k);
    X = pv(:,p,:)./sum(pv, 2, 'omitnan')*100;
    X = squeeze(X);
    % X = detrend(X, 'omitnan');
    C(:,:,k) = corr(X, rows='pairwise');
    %     for i=1:16
    %       for j=1:16
    %         w(i,j,k) = sum(isfinite(X(:,i)) & isfinite(X(:,j))) - 1;
    %       end
    %     end
    %
  end
  % w = w./sum(w,3);
  % C = sum(C.*w,3); 
  % C(1:17:end) = 1;
  C = mean(C, 3);
  R = corr_par(C, lander);
  [line, R] = dist_plot(C, D, R);
  R = tril(R, -1) + tril(R, -1)';
  %R = R - 0.01;
  R(1:17:end) = 1;
  fprintf('Distance–correlation relationship, west: ')
  fprintf('C = %.2f – %.5f×(distance in km)\n', line(2), -line(1))
end

function heading(h), fprintf('\n%s:\n', h), end
function dispsingle(h, x), fprintf('%s: %.2f\n', h, x), end

function [line, R] = dist_plot(C, D, R)
  figure(5), clf
  ax = gca();
  xlabel('Distance between geographic centers of the Länder, km')
  ylabel('Average correlation')
  axis([0,640,0.50,1])
  set(ax, 'ytick', 0.5:0.1:1)
  set(ax, 'TitleFontWeight', 'normal')
  save_fig()
  Dwest = vecl(D(1:10, 1:10));
  Cwest = vecl(C(1:10,1:10));
  [~, edges, bins] = histcounts(Dwest, [0:100:500, 700]);
  line = polyfit(Dwest, Cwest, 1);
  X = [0, 650];
  Y = polyval(line, X);
  hold on
  ax.XLim = X;
  ax.YLim = [0.7, 1];
  plot(Dwest, Cwest, '.', markersize=15, color=rgb('brown'))
  plot(X, Y, color=[rgb('darkgray') 0.6], linewidth=5)
  tightaxis([0,0,5,10])
  for k=1:length(edges)-1
    correl = Cwest(bins==k);
    hdr = sprintf("West-West, %d–%d km", edges(k), edges(k+1));
    dispsingle(hdr, mean(correl, 'all'))
  end
  for i=1:10
    for j=1:i-1
      R(i,j) = round(polyval(line, D(i,j)), 2);
    end
  end
end

function R = corr_par(C, lander)
  BBS = 8:10;
  BTS = [13, 15, 16];
  disp('BBS, BTS:')
  disp(lander(BBS))
  disp(lander(BTS))
  other7 = 1:7;
  Berlin = 11;
  other2 = setdiff(12:16, BTS);
  west_groups = {BBS, other7, Berlin};
  east_groups = {BTS, other2, Berlin};
  west = unique([other7, BBS]);
  east = unique([BTS, other2]);
  for i=1:3
    G1 = west_groups{i};
    for j=1:3
      G2 = east_groups{j};
      M = round(mean(C(G1, G2), 'all'), 3);
      table3(i,j) = M;
      R(G2, G1) = M;
    end    
  end
  heading('Table 3 (BBS, other 7, Berlin vs. BTS, other2, Berlin)')
  show(table3, '-d2')
  for i=1:2
    G = east_groups{i};
    tableEE(i,i) = round(mean(vecl(C(G,G))), 3);
  end
  tableEE(2,1) = round(mean(C(east_groups{1}, east_groups{2}), 'all'), 3);
  tableEE(1,2) = tableEE(2,1);
  heading('Table 2 (within East; BTS, other2, Berlin)')
  show(tableEE, '-d2')
  meaneast = round(mean(vecl(C(east, east))), 3);
  dispsingle('East-East', meaneast)
  dispsingle('West-West', mean(vecl(C(west, west))))
  R(east, east) = meaneast;
  R(BTS, Berlin) = table3(3, 1);
  R(other2, Berlin) = table3(3, 2);
end

function p = RSD_plot(vote_share, litir, flokkar, titill, SEL, fig, nr)
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
  %yt = RSD_interp(t, c0, c40);
  xmax = 50;
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
  ylabel('Relative standard deviation, %')
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
% 1/0.293). With scatter the marker size is measured as the area of a square with
% the same diameter as the o marker, so for a gscatter marker . of size 20 the
% corresponding scatter marker would be o of size (0.293x20)^2 = 34.



