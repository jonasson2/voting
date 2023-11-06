function b = broken_line_regress(x, y, breaks, varargin)
  [ZERO, W] = getKeywordParams(zero=false, weight=0);
  % specify zero=true to force regression to go through (0,0)
  x = x(:); y = y(:); breaks = breaks(:);
  I = ~isnan(x) & ~isnan(y) & x >= 0;
  if any(x > breaks(end))
    breaks(end+1, 1) = max(x);
  end
  x = x(I);
  y = y(I);
  if ZERO, breaks = [0; breaks]; end
  d = diff(breaks);
  [x,J] = sort(x);
  y = y(J);
  if ZERO
    X = zeros(length(x), 0);
  else
    X = [max(0, (breaks(2) - x)/d(1))];
  end
  for i=2:length(breaks)-1
    X(:,end+1) = max(0, min((x - breaks(i-1))/d(i-1), (breaks(i+1) - x)/d(i)));
  end
  X(:,end+1) = max(0, (x - breaks(end-1))/d(end));
  if W
    v = lscov(X, y, W);
  else
    v = lscov(X, y);
  end
  if ZERO
    v = [0; v];
  end
  b = griddedInterpolant(breaks, v);
end
