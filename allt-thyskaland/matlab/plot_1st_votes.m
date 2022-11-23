function plot_1st_votes()
  [pv, cv, flokkar, lond, litir] = read_votes();
  DROP = ismember(flokkar, ["PDS", "AfD"]);
  votesum = sum(pv,2,'omitnan');
  vsp = squeeze(mean(pv./votesum, 'omitnan'));
  vsc = const_vote_share(cv);
  for l=1:16
    vsc{l}(:,DROP,:) = [];
  end
  flokkar(DROP) = [];
  cv(DROP) = [];
  pv(:,DROP,:) = [];
  vsp(DROP, :) = [];
  litir(DROP, :) = [];
  [nparty, nland] = size(vsp);
  figure(1)
  clf
  for p=1:nparty
    for l=1:nland
      P = squeeze(pv(:,p,l));
      C = cv{p}{l};
      nyr = sum(isfinite(C));
      J = nyr >= 3;
      w = (nyr(J) - 2); w = w/sum(w);
      n_corr(p,l) = sum(J);
      corrpl = corr(P, C(:,J), rows='pairwise');
      scatter(vs{l}(p,:), corrpl, 'o', 'filled', markersize=77, ...
        markerfacecolor=litir(:,p))
      avg_corr(p,l) = sum(w.*corrpl);
    end
  end
  grp = repmat((1:nparty)', 1, nland);
  avg_corr(avg_corr < 0) = NaN;
  gscatter(vsp(:), avg_corr(:), grp(:), litir, [], 30)
end

function vs = const_vote_share(cv)
  % cv is nparty by nland cell array of nconst{p}{l} dimensional vectors
  np = length(cv);
  nl = 16;
  for l=1:nl
    clear cvl
    for p=1:np
       cvl(:,p,:) = cv{p}{l}; %#ok<AGROW> 
    end
    vote_shares = cvl./sum(cvl, 2, 'omitnan');
    vs{l} = squeeze(mean(vote_shares, 'omitnan'));
  end
end